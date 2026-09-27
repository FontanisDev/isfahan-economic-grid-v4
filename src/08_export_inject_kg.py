import pandas as pd
import geopandas as gpd
import h3
import numpy as np
import requests
from shapely.geometry import Polygon
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, SKOS

print("=== 1. Loading Province Predictions ===")
df = pd.read_csv("data/OSM/h3_res9_final_predictions.csv")

comp_cols = [c for c in df.columns if c.startswith('comp_')]
df = df.copy()
df['total_activity'] = df[comp_cols].sum(axis=1)
active_df = df[df['total_activity'] > 0].copy()

print(f"Total cells: {len(df)}")
print(f"Active economic nodes: {len(active_df)}")

# Check distribution across cities
cities = {
    'Isfahan': ((32.54, 32.83), (51.52, 51.86)),
    'Najafabad': ((32.59, 32.68), (51.35, 51.50)),
    'Shahinshahr': ((32.83, 32.93), (51.50, 51.60)),
    'Mobarakeh': ((32.30, 32.40), (51.45, 51.55)),
    'Fooladshahr': ((32.55, 32.65), (51.40, 51.50))
}

print("\nDistribution by city:")
for city, ((lat_min, lat_max), (lon_min, lon_max)) in cities.items():
    count = len(active_df[
        (active_df['lat'] >= lat_min) & (active_df['lat'] <= lat_max) &
        (active_df['lon'] >= lon_min) & (active_df['lon'] <= lon_max)
    ])
    print(f"  {city}: {count} active nodes")

print("\n=== 2. Generating GeoJSON for QGIS ===")
def get_poly(cell):
    boundary = h3.cell_to_boundary(cell)
    return Polygon([(p[1], p[0]) for p in boundary])

active_df['geometry'] = active_df['h3_cell'].apply(get_poly)
gdf = gpd.GeoDataFrame(active_df, geometry='geometry', crs="EPSG:4326")

keep_cols = ['h3_cell', 'lat', 'lon', 'total_activity', 'geometry'] + comp_cols
gdf_out = gdf[keep_cols].copy()
gdf_out.to_file("data/OSM/v4_province_economic_nodes.geojson", driver="GeoJSON")
print("Saved data/OSM/v4_province_economic_nodes.geojson")

print("\n=== 3. Building Knowledge Graph (RDF) ===")
ISF = Namespace("http://isfahan-wealth-flow.local/")
UNSPSC = Namespace("http://ontoview.org/schema/unspsc/1/")

g = Graph()
g.bind("isf", ISF)
g.bind("unspsc", UNSPSC)
g.bind("skos", SKOS)

for _, row in active_df.iterrows():
    cell_uri = ISF[f"Node_{row['h3_cell']}"]
    g.add((cell_uri, RDF.type, ISF["EconomicNode"]))
    g.add((cell_uri, ISF["lat"], Literal(row['lat'])))
    g.add((cell_uri, ISF["lon"], Literal(row['lon'])))
    g.add((cell_uri, ISF["totalActivity"], Literal(row['total_activity'])))
    
    for col in comp_cols:
        val = row[col]
        if val > 0.05:
            fam_code = col.replace('comp_', '')
            fam_uri = UNSPSC[f"Family_{fam_code}"]
            g.add((cell_uri, ISF["hasSector"], fam_uri))
            g.add((cell_uri, ISF[f"pct_{fam_code}"], Literal(float(val))))

print(f"Generated {len(g)} triples.")

print("\n=== 4. Injecting into Fuseki ===")
# First clear old data
clear_url = "http://localhost:3030/isfahan_wealth/update"
clear_query = "CLEAR GRAPH <http://isfahan-wealth-flow.local>"
headers = {"Content-Type": "application/sparql-update"}

try:
    requests.post(clear_url, data=clear_query, headers=headers, auth=('admin', 'admin'))
    print("Cleared old v4 data from Fuseki")
    
    fuseki_url = "http://localhost:3030/isfahan_wealth/data"
    headers = {"Content-Type": "text/turtle"}
    ttl_data = g.serialize(format="turtle")
    
    response = requests.post(fuseki_url, data=ttl_data, headers=headers, auth=('admin', 'admin'))
    print(f"Fuseki response: {response.status_code}")
    if response.status_code == 200:
        print("SUCCESS: Injected province-wide v4 economic nodes into Knowledge Graph.")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Connection error: {e}. Is Fuseki running?")

