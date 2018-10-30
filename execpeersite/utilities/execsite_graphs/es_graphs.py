from plotly.offline import plot
from plotly import graph_objs as go


def sankey_diagram(org_conn_records):
    def process_conn_set(exchange_name, exchange_index, conn_set, src=None):
        org_index = conn_set[0]
        # Convert capacity from Mbps to Gbps
        capacity = conn_set[2] / 1000
        if src == 'Organization':
            if exchange_name in data['node']['label']:
                data['link']['source'].append(org_index)
                data['link']['target'].append(exchange_index)
                data['link']['value'].append(capacity)
            else:
                data['node']['label'].append(exchange_name)
                data['link']['source'].append(org_index)
                data['link']['target'].append(exchange_index)
                data['link']['value'].append(capacity)
        elif src == 'Exchange':
            if exchange_name in data['node']['label']:
                data['link']['target'].append(org_index)
                data['link']['source'].append(exchange_index)
                data['link']['value'].append(capacity)
            else:
                data['node']['label'].append(exchange_name)
                data['link']['target'].append(org_index)
                data['link']['source'].append(exchange_index)
                data['link']['value'].append(capacity)

    def process_exchange_records(exchange_entry, src=None):
        exchange_index = exchange_entry[0]
        exchange_name = exchange_entry[1][0]
        conn_sets = exchange_entry[1][1]

        # Manage exchanges that are explicit in src/tgt (i.e. All index even or odd)
        if src == 'Organization':
            for conn_set in conn_sets:
                process_conn_set(exchange_name, exchange_index, conn_set, src=src)
        elif src == 'Exchange':
            for conn_set in conn_sets:
                process_conn_set(exchange_name, exchange_index, conn_set, src=src)

        # Manage exchanges that are connected to multiple organizations
        elif not src:
            if len(conn_sets) > 1:
                for conn_set in conn_sets:
                    org_index = conn_set[0]
                    # Process even index, place org on source side of diagram
                    if not org_index % 2:
                        process_conn_set(exchange_name, exchange_index, conn_set, src='Organization')
                    # Process odd index, place org on target side of diagram
                    else:
                        process_conn_set(exchange_name, exchange_index, conn_set, src='Exchange')

            # Manage exchanges that are connected to a single organization
            elif len(conn_sets) == 1:
                for conn_set in conn_sets:
                    org_index = conn_set[0]
                    # Process even index, place org on target side of diagram
                    if not org_index % 2:
                        process_conn_set(exchange_name, exchange_index, conn_set, src='Exchange')
                    # Process odd index, place org on source side of diagram
                    else:
                        process_conn_set(exchange_name, exchange_index, conn_set, src='Organization')

    data_input = {}
    # Use dict to get a unique set of keys (exchanges) for all organizations
    for i, org_conn_record in enumerate(org_conn_records):
        org_record = org_conn_record[0]
        conn_record = org_conn_record[1]
        for conn in conn_record:
            conn_set = [(i, org_record.name, conn.capacity)]
            if conn.exchange_point in data_input:
                data_input[conn.exchange_point].extend(conn_set)
            else:
                data_input.update({conn.exchange_point: conn_set})

    data = dict(
        type='sankey',
        orientation="h",
        valueformat=',3r',
        valuesuffix=' Gbps',
        hoverinfo='text',
        node=dict(
            pad=6,
            thickness=10,
            line=dict(
                color="black",
                width=0.5
            ),
            label=[org_record.name for org_record, conn_record in org_conn_records],
        ),
        link=dict(
            source=[],
            target=[],
            value=[],
        ))

    for exchange in enumerate(data_input.items(), len(org_conn_records)+1):
        '''
        Logic:
        Exchanges connected to Multiple Organizations:
            - Manage even index and odd index organizations by placing them on opposite sides of diagram
            - If even index, place organization on source side of diagram
            - If odd index, place organization on target side of diagram
            - If an exchange is connected to all even index organizations, 
                place organization on target side of diagram
            - If an exchange is connected to all odd index organizations, 
                place organization on source side of diagram
        
        Exchanges connected to Single Organization:
            - If even index, place organization on target side of diagram
            - If odd index, place organization on source side of diagram
        '''
        # Manage exchanges that are connected to multiple organizations
        conn_sets = exchange[1][1]

        if len(conn_sets) > 1:
            # If index is even, place org on source side of diagram
            # Unless ALL index are even for exchange; place org on target side of diagram
            if all(not conn_set[0] % 2 for conn_set in conn_sets):
                process_exchange_records(exchange, src='Exchange')
                continue
            # If index is odd, place org on source side of diagram
            # Unless ALL index are odd for exchange; place org on target side of diagram
            elif all(conn_set[0] % 2 for conn_set in conn_sets):
                process_exchange_records(exchange, src='Organization')
                continue

        process_exchange_records(exchange)

    layout = dict(
        font=dict(
          size=10

        ),
        autosize=True
    )

    fig = go.Figure(data=[data], layout=layout)
    div = plot(fig, auto_open=False, output_type='div', include_plotlyjs=False)
    return div
