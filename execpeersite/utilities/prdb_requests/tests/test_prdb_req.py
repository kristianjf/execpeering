import responses
import json
from decouple import config
from prdb_req import Organization
'''
Test functions in the prdb_request module:
- class: Organization
  - Organization.retrieve()
    - method: retrieve(path)
    - method: retrieve(path, **kwargs)
    - method: retrieve(path, json_return)
    - method: retrieve(path, json_return, **kwargs)
  - Organization.PeerOrganization()
    - Test Cases:
      - patch variable:ixlan_set - self.retrieve function with result that returns a netixlan_set with the following:
        - At least two IX's that belong to the same organization
        - At least one IX that does not belong to the same organization 
        - At least one IX that has two connections
    - return org_peer_dict
    org_peer_dict[org_name] = {
                    'org_id': org_id,
                    'peer_set': [{peer_name: {'conn_count': 1, 'capacity': new_peer_speed}}],
                    'ix_set': ix_set,
                }
  - Organization.metrics()
    - Test the following variables:
      - self.total_peers
      - self.total_speed
      - self.peer_info[org].total_po_peers
      - self.peer_info[org].total_po_speed
      
    
'''

PEERING_DB_USER = config('PEERING_DB_USER')
PEERING_DB_PASS = config('PEERING_DB_PASS')
PEERING_DB_URL = f'https://{PEERING_DB_USER}:{PEERING_DB_PASS}@peeringdb.com/api'
JSON_DATA = json.load(open('tests/data/prdb_net_1956', 'r'))


@responses.activate
def test_retrieve(path='/net/1956'):
    responses.add(responses.GET, f'{PEERING_DB_URL}{path}', json=JSON_DATA, status=200)
    result = Organization.retrieve(path)
    assert result['id'] == 1956
    assert result['name'] == 'Twitch'
    assert result['asn'] == 46489
    assert isinstance(result['netixlan_set'], list)


@responses.activate
def test_retrieve_params(path='/net/1956'):
    responses.add(responses.GET, f'{PEERING_DB_URL}{path}', json=JSON_DATA, status=200)
    result = Organization.retrieve(path, json_return=['netixlan_set'])[0]
    assert 'Equinix Los Angeles' in [peer_set['name'] for peer_set in result]
    assert 10000 in [peer_set['speed'] for peer_set in result]
    assert 4 in [peer_set['ix_id'] for peer_set in result]


def test_retrieve_json_return():
    pass


@responses.activate
def test_retrieve_params_json_return(path='/net'):
    responses.add(responses.GET, f'{PEERING_DB_URL}{path}', json=JSON_DATA, status=200)
    asn, net_id = Organization.retrieve(path, json_return=['asn', 'id'], name__in='Twitch')
    assert asn == 46489
    assert net_id == 1956
