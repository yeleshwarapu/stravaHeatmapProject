import osmnx as ox
import networkx as nx
import gpxpy
import gpxpy.gpx
import random

# --- CONFIG ---
CITY = "San Jose, California, USA"
NEIGHBORHOOD = "Willow Glen, San Jose, California, USA"
CHUNK_DISTANCE_METERS = 16093.4  # 10 miles
INITIAL_RADIUS = 2500
MAX_RADIUS = 12000
RADIUS_STEP = 1000
MIN_ROUTE_DISTANCE = 0.9 * CHUNK_DISTANCE_METERS
MAX_ROUTE_DISTANCE = 1.1 * CHUNK_DISTANCE_METERS

# --- Load Graph ---
print("Downloading full city graph...")
G = ox.graph_from_place(CITY, network_type='bike', simplify=True)
G = G.to_undirected()

# --- Pick Start Node from Neighborhood ---
print(f"Getting start node from {NEIGHBORHOOD}...")
subgraph = ox.graph_from_place(NEIGHBORHOOD, network_type='bike', simplify=True)
start_node = random.choice(list(subgraph.nodes))
print(f"Starting at node: {start_node}")

# --- Utilities ---
def route_length(G, route):
    return sum(G.edges[route[i], route[i + 1], 0]['length'] for i in range(len(route) - 1))

def route_to_gpx(G, route):
    gpx = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(track)
    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)
    for node in route:
        pt = G.nodes[node]
        segment.points.append(gpxpy.gpx.GPXTrackPoint(pt['y'], pt['x']))
    return gpx.to_xml()

def smart_random_walk(G_sub, start_node, used_edges):
    for attempt in range(300):  # try multiple walks
        route = [start_node]
        current_node = start_node
        total_distance = 0
        local_edges = set()

        for _ in range(1000):
            neighbors = list(G_sub.neighbors(current_node))
            if not neighbors:
                break
            random.shuffle(neighbors)

            # Sort by preference: unused edges first
            neighbors.sort(key=lambda n: ((current_node, n) in used_edges or (n, current_node) in used_edges))

            found = False
            for neighbor in neighbors:
                edge = (current_node, neighbor)
                rev_edge = (neighbor, current_node)
                if G_sub.has_edge(*edge):
                    edge_data = G_sub.edges[edge[0], edge[1], 0]
                elif G_sub.has_edge(*rev_edge):
                    edge_data = G_sub.edges[rev_edge[0], rev_edge[1], 0]
                else:
                    continue

                length = edge_data['length']
                if total_distance + length > MAX_ROUTE_DISTANCE:
                    continue

                # Accept even if previously used (but try to avoid)
                total_distance += length
                route.append(neighbor)
                current_node = neighbor
                local_edges.add(edge)
                found = True
                break

            if not found or total_distance >= MIN_ROUTE_DISTANCE:
                break

        if total_distance >= MIN_ROUTE_DISTANCE:
            print(f"✅ Route found: {total_distance / 1609:.2f} miles, steps: {len(route)}")
            return route, local_edges

    print("⚠️ Could not find valid route within distance constraints.")
    return None, None

# --- Main Loop ---
used_edges = set()
current_node = start_node
route_count = 1

while True:
    found_route = False

    for radius in range(INITIAL_RADIUS, MAX_RADIUS + RADIUS_STEP, RADIUS_STEP):
        print(f"🔍 Searching radius {radius}m from node {current_node}...")

        G_sub = ox.truncate.truncate_graph_dist(G, current_node, dist=radius)

        route, new_edges = smart_random_walk(G_sub, current_node, used_edges)

        if route:
            gpx_data = route_to_gpx(G, route)
            filename = f"explore_san_jose_{route_count}.gpx"
            with open(filename, "w") as f:
                f.write(gpx_data)

            miles = route_length(G, route) / 1609
            print(f"📦 Saved {filename} — {miles:.2f} miles")

            used_edges.update(new_edges)
            current_node = route[-1]
            route_count += 1
            found_route = True
            break  # proceed to next route

    if not found_route:
        print("❌ No more good paths. Exploration complete.")
        break
