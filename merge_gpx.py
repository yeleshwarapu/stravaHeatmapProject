import gpxpy
import os
import numpy as np
from sklearn.cluster import DBSCAN
from geopy.geocoders import Nominatim
from geopy.distance import great_circle
from time import sleep

# === Config ===
gpx_folder = "activities"
output_folder = "gpx_output"
distance_threshold_meters = 1000000

geolocator = Nominatim(user_agent="gpx_cluster_namer")

# === Load GPX files ===
gpx_files = [f for f in os.listdir(gpx_folder) if f.endswith('.gpx')]
tracks = []
coords = []

for f in gpx_files:
    with open(os.path.join(gpx_folder, f), 'r') as file:
        gpx = gpxpy.parse(file)
        if gpx.tracks:
            track = gpx.tracks[0]
            first_point = track.segments[0].points[0]
            coords.append([first_point.latitude, first_point.longitude])
            tracks.append((f, gpx, (first_point.latitude, first_point.longitude)))

# === Cluster ===
coords_rad = np.radians(coords)
epsilon = distance_threshold_meters / 6371000.0

clustering = DBSCAN(eps=epsilon, min_samples=1, algorithm='ball_tree', metric='haversine')
labels = clustering.fit_predict(coords_rad)

# === Group by cluster ===
cluster_dict = {}
cluster_centers = {}

for label, (fname, gpx, coord) in zip(labels, tracks):
    cluster_dict.setdefault(label, []).append((fname, gpx))
    cluster_centers.setdefault(label, []).append(coord)

# === Reverse geocode each cluster center to get location name ===
os.makedirs(output_folder, exist_ok=True)
used_names = set()


def safe_location_name(lat, lon):
    try:
        location = geolocator.reverse((lat, lon), exactly_one=True, language='en')
        if location:
            components = location.raw.get("address", {})
            for key in ["city", "town", "village", "state", "country"]:
                if key in components:
                    name = components[key]
                    break
            else:
                name = "Unknown"
        else:
            name = "Unknown"
    except Exception as e:
        name = "Unknown"
    return name.replace(" ", "_")


for label, items in cluster_dict.items():
    # Average location
    lat, lon = np.mean(cluster_centers[label], axis=0)
    name = safe_location_name(lat, lon)

    # Handle duplicates
    base_name = name
    i = 1
    while name in used_names:
        name = f"{base_name}_{i}"
        i += 1
    used_names.add(name)

    # Write GPX
    new_gpx = gpxpy.gpx.GPX()
    for _, gpx in items:
        for track in gpx.tracks:
            new_gpx.tracks.append(track)
    out_path = os.path.join(output_folder, f"{name}.gpx")
    with open(out_path, "w") as f:
        f.write(new_gpx.to_xml())

    print(f"Created: {name}.gpx")

    # Be nice to the API
    sleep(1)

print("✅ Finished grouping and naming GPX files by location.")
