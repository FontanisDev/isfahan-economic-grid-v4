import json
from osmium import SimpleHandler

class POIHandler(SimpleHandler):
    def __init__(self):
        self.pois = []
        self.tags_of_interest = ['amenity', 'shop', 'office', 'tourism', 'craft', 'healthcare', 'leisure']
    
    def node(self, n):
        for tag in self.tags_of_interest:
            if tag in n.tags:
                self.pois.append({
                    'lat': n.location.lat,
                    'lon': n.location.lon,
                    'category': f"{tag}_{n.tags[tag]}"
                })
                break

handler = POIHandler()
handler.apply_file("data/OSM/isfahan_correct.pbf")

with open("data/OSM/isfahan_correct_pois.json", "w", encoding="utf-8") as f:
    json.dump(handler.pois, f, ensure_ascii=False)

print(f"Extracted {len(handler.pois)} POIs from new PBF")
