import osmnx as ox
import networkx as nx
import gpxpy
import gpxpy.gpx
import random

# --- CONFIG ---
CITY = "San Jose, California, USA"
CHUNK_DISTANCE_METERS = 16093.4  # 10 miles
NUM_ROUTES = 20
START_LOCATION = (37.3352, -121.8811)  # Downtown San Jose

# --- Load San Jose's road network ---
print("Downloading road network...")
G = ox.graph_from_place(CITY, network_type='bike', simplify=True)
G = G.to_undirected()

# --- Helper functions ---

def route_length(G, route):
    return sum(G.edges[route[i], route[i + 1], 0]['length'] for i in range(len(route) - 1))

def route_to_gpx(G, route):
    gpx = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(track)
    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)
    for node in route:
        point = G.nodes[node]
        segment.points.append(gpxpy.gpx.GPXTrackPoint(point['y'], point['x']))
    return gpx.to_xml()

def find_next_node_far_enough(G, from_node, min_distance_m=CHUNK_DISTANCE_METERS * 0.9, max_attempts=100):
    nodes = list(G.nodes)
    for _ in range(max_attempts):
        candidate = random.choice(nodes)
        try:
            path = nx.shortest_path(G, from_node, candidate, weight='length')
            dist = route_length(G, path)
            if dist >= min_distance_m:
                return candidate
        except nx.NetworkXNoPath:
            continue
    return None

# --- Start routing ---
current_node = ox.nearest_nodes(G, START_LOCATION[1], START_LOCATION[0])

for i in range(1, NUM_ROUTES + 1):
    print(f"🔄 Generating route {i} from node {current_node}...")

    target_node = find_next_node_far_enough(G, current_node)
    if not target_node:
        print("⚠️ Could not find a long enough route. Picking random new start.")
        current_node = random.choice(list(G.nodes))
        continue

    try:
        route = nx.shortest_path(G, current_node, target_node, weight='length')
        distance = route_length(G, route)
    except nx.NetworkXNoPath:
        print("❌ No path found. Skipping this route.")
        continue

    if len(route) < 2 or distance < CHUNK_DISTANCE_METERS * 0.9:
        print("⚠️ Route too short. Skipping.")
        continue

    # Save to GPX
    gpx_data = route_to_gpx(G, route)
    filename = f"explore_san_jose_{i}.gpx"
    with open(filename, "w") as f:
        f.write(gpx_data)

    print(f"✅ Saved {filename} ({distance/1609:.2f} miles)")
    current_node = route[-1]  # Continue from where this one ended

print("🎉 Done generating all routes!")
