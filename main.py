import osmnx as ox
from utils import *

# --- CONFIG ---
CITY = "San Jose, California, USA"
MILES = 20 # 20 miles
CHUNK_DISTANCE_METERS = MILES*1.609*1000
INITIAL_RADIUS = 2500
MAX_RADIUS = 15000
RADIUS_STEP = 1000
MIN_ROUTE_DISTANCE = 0.9 * CHUNK_DISTANCE_METERS
MAX_ROUTE_DISTANCE = 1.1 * CHUNK_DISTANCE_METERS

# --- Load Graph ---


# --- Main Loop ---
def main():
    print("Downloading San Jose road network...")
    G = ox.graph_from_place(CITY, network_type='bike', simplify=True)
    G = G.to_undirected()
    used_edges = set()
    route_count = 1
    current_node = random.choice(list(G.nodes))  # Start randomly
    while True:
        found_route = False

        for radius in range(INITIAL_RADIUS, MAX_RADIUS + RADIUS_STEP, RADIUS_STEP):
            print(f"\n🔍 Searching radius {radius}m from node {current_node}...")

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
                break

        if not found_route:
            print("🔄 Stuck — picking a new unexplored start node...")
            new_node = get_random_unexplored_node(G, used_edges)
            if new_node is None:
                print("❌ No more viable unexplored areas left. Exploration complete.")
                break
            else:
                print(f"🧭 New start node: {new_node}")
                current_node = new_node

if __name__ == main():
    main()