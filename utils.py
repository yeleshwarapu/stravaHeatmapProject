import gpxpy
import gpxpy.gpx
import random

MILES = 20 # 20 miles
CHUNK_DISTANCE_METERS = MILES*1.609*1000
MIN_ROUTE_DISTANCE = 0.9 * CHUNK_DISTANCE_METERS
MAX_ROUTE_DISTANCE = 1.1 * CHUNK_DISTANCE_METERS


def route_length(graph, route):
    ## route is a list of nodes (e.g., [A, B, C]).
    ## loops over adjacent pairs: (A, B), (B, C)
    ## each edge between consecutive nodes, it grabs the 'length' attribute from the graph's edge data.
    ## sums up these lengths and returns the total
    return sum(graph.edges[route[i], route[i + 1], 0]['length'] for i in range(len(route) - 1))

def route_to_gpx(graph, route):
    gpx = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(track)
    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)
    for node in route:
        pt = graph.nodes[node]
        segment.points.append(gpxpy.gpx.GPXTrackPoint(pt['y'], pt['x']))
    return gpx.to_xml()

def smart_random_walk(G_sub, start_node, used_edges):
    for attempt in range(300):  # Try multiple walks
        route = [start_node]
        current_node = start_node
        total_distance = 0
        local_edges = set()

        for _ in range(1500):  # Max steps per walk
            neighbors = list(G_sub.neighbors(current_node))
            if not neighbors:
                break
            random.shuffle(neighbors)
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

def get_random_unexplored_node(G, used_edges, tries=200):
    nodes = list(G.nodes)
    for _ in range(tries):
        candidate = random.choice(nodes)
        neighbors = list(G.neighbors(candidate))
        unexplored = [
            (candidate, n) for n in neighbors
            if (candidate, n) not in used_edges and (n, candidate) not in used_edges
        ]
        if len(unexplored) / max(len(neighbors), 1) > 0.5:
            return candidate
    return None
