import requests
import os
if os.path.exists("data/OSM/isfahan_correct.pbf"):
    print("PBF already exists. Skipping download.")
    raise SystemExit(0)

# Bounding box: Rezvanshahr to Shahid Beheshti Airport, Shahinshahr to Mobarakeh
# S=32.30, W=51.05, N=32.90, E=51.80
bbox = "32.30,51.05,32.90,51.80"

overpass_url = "http://overpass-api.de/api/interpreter"
query = f"""
[out:xml][timeout:300];
(
  node({bbox});
  way({bbox});
  relation({bbox});
);
out body;
>;
out skel qt;
"""

print("Downloading PBF from Overpass API...")
print(f"Bounding box: S=32.30, W=51.05, N=32.90, E=51.80")
print("This may take 5-10 minutes...")

headers = {
    'User-Agent': 'IsfahanWealthFlow/4.0',
    'Accept': 'application/xml, text/xml'
}

response = requests.post(overpass_url, data={"data": query}, headers=headers, timeout=600)

if response.status_code == 200:
    with open("data/OSM/isfahan_correct.osm", "wb") as f:
        f.write(response.content)
    print(f"Downloaded OSM XML file ({len(response.content)} bytes)")
    
    # Convert to PBF using osmium
    import subprocess
    result = subprocess.run([
        "osmium", "cat",
        "data/OSM/isfahan_correct.osm",
        "-o", "data/OSM/isfahan_correct.pbf"
    ], capture_output=True)
    
    if result.returncode == 0:
        print("Converted to PBF format successfully")
        print("New PBF saved to data/OSM/isfahan_correct.pbf")
    else:
        print(f"osmium error: {result.stderr.decode()}")
else:
    print(f"Error: {response.status_code}")
    print(response.text[:500])
