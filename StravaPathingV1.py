import osmnx as ox
import networkx as nx
import gpxpy.gpx as gpxpy
from networkx.algorithms.euler import eulerian_circuit

# --- CONFIG ---
CITY = "San Jose, California, USA"
START_LOCATION = (37.3352, -121.8811)  # Default: Downtown San Jose

# --- Step 1: Load graph ---
print("Downloading road network...")
G = ox.graph_from_place(CITY, network_type='bike')
G = nx.Graph(G)  # Convert to undirected NetworkX graph

# --- Step 2: Find Eulerian circuit ---
# The idea is to duplicate some edges to make all node degrees even, so a complete path exists
print("Solving route inspection problem (Chinese Postman)...")
augmented_graph = nx.algorithms.euler.eulerize(G.copy())
circuit = list(eulerian_circuit(augmented_graph))

# --- Step 3: Convert circuit to node path ---
route = [circuit[0][0]] + [v for u, v in circuit]

# --- Step 4: Convert to GPX ---
def route_to_gpx(G, route):
    gpx = gpxpy.GPX()
    gpx_track = gpxpy.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    for node in route:
        point = G.nodes[node]
        gpx_segment.points.append(gpxpy.GPXTrackPoint(point['y'], point['x']))

    return gpx.to_xml()

# --- Step 5: Export ---
print("Exporting full city coverage route to GPX...")
gpx_data = route_to_gpx(G, route)

with open("san_jose_full_coverage.gpx", "w") as f:
    f.write(gpx_data)

print("Done! GPX file saved as san_jose_full_coverage.gpx")
