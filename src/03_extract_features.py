import json
from osmium import SimpleHandler
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
import shapely.wkt

class FeatureHandler(SimpleHandler):
    def __init__(self):
        self.features = []
    
    def way(self, w):
        tags = dict(w.tags)
        if 'building' in tags or 'landuse' in tags:
            try:
                coords = [(n.lon, n.lat) for n in w.nodes]
                if len(coords) >= 3:
                    geom = Polygon(coords)
                    if geom.is_valid:
                        feature = {
                            'type': 'Feature',
                            'properties': tags,
                            'geometry': geom.__geo_interface__
                        }
                        self.features.append(feature)
            except:
                pass

print("Extracting buildings and landuse from new PBF...")
handler = FeatureHandler()
handler.apply_file("data/OSM/isfahan_correct.pbf", locations=True)

gdf = gpd.GeoDataFrame.from_features(handler.features, crs="EPSG:4326")
gdf.to_file("data/OSM/isfahan_correct_all.geojson", driver="GeoJSON")

print(f"Extracted {len(gdf)} features")
print(f"  Buildings: {gdf['building'].notna().sum()}")
print(f"  Landuse: {gdf['landuse'].notna().sum()}")
