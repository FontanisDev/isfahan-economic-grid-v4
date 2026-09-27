import geopandas as gpd
from rdflib import Graph
from rdflib.namespace import SKOS

print("Loading family titles...")
g = Graph()
g.parse("ontology/unspsc_full.ttl", format="turtle")

titles = {}
for s, p, o in g:
    if p == SKOS.prefLabel and "Family_" in str(s):
        titles[str(s).split("Family_")[-1]] = str(o)

print("Adding dominant sector name...")
gdf = gpd.read_file("data/OSM/v4_province_economic_nodes.geojson")
comp = [c for c in gdf.columns if c.startswith("comp_")]

gdf["dominant_code"] = gdf[comp].idxmax(axis=1).str.replace("comp_", "")
gdf["dominant_pct"] = (gdf[comp].max(axis=1) * 100).round(1)
gdf["dominant_name"] = gdf["dominant_code"].map(titles).fillna("Unknown")

gdf.to_file("data/OSM/v4_province_economic_nodes.geojson", driver="GeoJSON")
print("Province GeoJSON updated with names.")
