#!/usr/bin/python3
'''

Module to retrieve org, net, ix data from PeeringDB
'''
import requests
import logging
from decouple import config

PEERING_DB_USER = config('PEERING_DB_USER')
PEERING_DB_PASS = config('PEERING_DB_PASS')
PEERING_DB_URL = f'https://{PEERING_DB_USER}:{PEERING_DB_PASS}@peeringdb.com/api'
LOGGER = logging.getLogger('__name__')


class Organization:

    @staticmethod
    def retrieve(path, json_return=None, **kwargs):
        """
        API Query to PeeringDB

        :param path: relative URL path to PeeringDB API root
        :param json_return: specify unpacked json values to return from web requests
        :param kwargs: requests parameters
        :return: unpacked json data
        """
        response = requests.get(f'{PEERING_DB_URL}{path}', params=kwargs)
        json_data = response.json()
        result = []
        if json_return:
            for val in json_return:
                result.append(json_data['data'][0].get(val))
            return result
        return json_data['data'][0]

    def __init__(self, org_name):
        """
        Initialize instance of Organization Class.
        :param org_name: Name to query from peering_db. Must be exact match.
        """
        self.org_name = org_name
        self.asn, self.net_id = self.retrieve('/net', json_return=['asn', 'id'], name__in=org_name)
        self.total_peers = int()
        self.total_exchanges = int()
        self.total_capacity = int()
        self.unique_orgs = int()
        self.peer_info = {}

    def PeerOrganization(self):
        """
        Populate top-level organization information and return peer information.
        :return: org_peer_dict[org_name] = {
                    'org_id': org_id,
                    'peer_set': [{peer_name: {'conn_count': 1, 'capacity': new_peer_speed}}],
                    'ix_set': ix_set,
                }
        """
        ixlan_set = self.retrieve(f'/net/{self.net_id}', json_return=['netixlan_set'])[0]
        org_peer_dict = {}
        for peer in ixlan_set:
            ix_id = peer['ix_id']
            peer_name, new_peer_speed = peer['name'], peer['speed']
            for org_name, org_data in org_peer_dict.items():
                # Use ix_id to determine if current peer record's organization is known.
                if ix_id in org_data['ix_set']:
                    LOGGER.warning(f'Organization is known {org_name}. Checking to see if peer known {peer_name}')
                    for peer_set in org_peer_dict[org_name]['peer_sets']:
                        if peer_name in peer_set:
                            LOGGER.warning(f'Peer is known {peer_name}. Updating existing peer entry')
                            current_peer_speed = peer_set[peer_name].get('capacity')
                            new_peer_speed += current_peer_speed
                            peer_set[peer_name].update({'capacity': new_peer_speed})
                            peer_set[peer_name]['conn_count'] += 1
                            break

                    else:
                        LOGGER.warning(f'Peer unknown {peer_name}. Creating new peer entry in organization {org_name}.')
                        org_peer_dict[org_name]['peer_sets'].append(
                        {peer_name: {'conn_count': 1, 'capacity': new_peer_speed}}
                        )
                    # As long as the organization (ix_id) is found, break any further organization query.
                    break

            else:
                # Query organization and create initial organization/peer record
                peer_name = peer['name']
                LOGGER.warning(f'Organization unknown for peer: {peer_name}. Querying PeeringDB')
                org, org_id = self.retrieve(f'/ix/{ix_id}', json_return=['org','org_id'])
                org_name = org.get('name')
                ix_set = org.get('ix_set')
                org_peer_dict[org_name] = {
                    'org_id': org_id,
                    'peer_sets': [{peer_name: {'conn_count': 1, 'capacity': new_peer_speed}}],
                    'ix_set': ix_set,
                }
        return org_peer_dict

    def peer_metrics(self):
        if not self.peer_info:
            self.peer_info = self.PeerOrganization()
        total_peers = int()
        total_capacity = int()
        total_exchanges = int()
        for org, org_data in self.peer_info.items():
            total_po_peers = sum([peer_data['conn_count'] for peer_set in org_data['peer_sets'] for peer_data in peer_set.values()])
            total_po_exchanges = sum([len(org_data['peer_sets'])])
            total_po_capacity = sum([peer_data['capacity'] for peer_set in org_data['peer_sets'] for peer_data in peer_set.values()])
            total_peers += total_po_peers
            total_exchanges += total_po_exchanges
            total_capacity += total_po_capacity
            self.peer_info[org].update({
                'total_po_peers': total_po_peers,
                'total_po_speed': total_po_capacity
            })
        self.total_peers = total_peers
        self.total_exchanges = total_exchanges
        self.total_capacity = total_capacity
        self.unique_orgs = len(self.peer_info)
