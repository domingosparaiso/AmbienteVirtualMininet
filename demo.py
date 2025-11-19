import networkx as nx

G = nx.Graph()
G.add_edges_from([
    ('H1', 'S1'),
    ('S1', 'S2'),
    ('S1', 'S4'),
    ('S2', 'S3'),
    ('S2', 'S5'),
    ('S3', 'S6'),
    ('S4', 'S5'),
    ('S5', 'S6'),
    ('S6', 'H2')
])

# Find all simple paths from node 0 to node 3
paths = list(nx.all_simple_paths(G, source='H1', target='H2'))