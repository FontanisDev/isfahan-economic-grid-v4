import h3
import json
import pandas as pd
import numpy as np
from rdflib import Graph, Namespace
from shapely.geometry import Polygon
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

print("=== 1. Loading UNSPSC Ontology (Family Level) ===")
g = Graph()
g.parse("ontology/unspsc_full.ttl", format="turtle")

SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
UNSPSC = Namespace("http://ontoview.org/schema/unspsc/1/")

family_map = {}
for s, p, o in g:
    if p == SKOS.prefLabel:
        uri_str = str(s)
        if "Family_" in uri_str:
            code = uri_str.split("Family_")[-1]
            family_map[code] = str(o)

print(f"Loaded {len(family_map)} UNSPSC Families from Ontology.")
family_labels = list(family_map.values())
family_codes = list(family_map.keys())

# ============================================================
# 2. AUTOMATED OSM -> UNSPSC MAPPING ENGINE
# ============================================================
print("\n=== 2. Building Automated Mapping Engine ===")

with open("data/OSM/pois_final_correct.json", "r", encoding="utf-8") as f:
    pois = json.load(f)

unique_tags = set(p['category'] for p in pois)
print(f"Found {len(unique_tags)} unique OSM categories to map.")

print("Loading semantic embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
family_labels_list = list(family_map.values())
family_codes_list = list(family_map.keys())
family_embeddings = model.encode(family_labels_list)

def find_best_family(osm_tag):
    parts = osm_tag.split('_')
    key = parts[0]
    val = '_'.join(parts[1:]).replace('_', ' ')
    
    # Translate common Persian OSM tags to English for the embedding model
    persian_map = {
        'فروشگاه مواد غذایی': 'grocery supermarket',
        'سوپرمارکت': 'supermarket',
        'نانوایی': 'bakery',
        'میوه فروشی': 'greengrocer fruit shop',
        'لوازم التحریر': 'stationery office supply',
        'پوشاک': 'clothing apparel',
        'آرایشگاه': 'hairdresser beauty salon',
        'تعویض روغن': 'car repair oil change',
        'کافی شاپ': 'cafe coffee shop',
        'رستوران': 'restaurant food'
    }
    for fa, en in persian_map.items():
        if fa in val:
            val = en
            break
            
    context = {
        'amenity': 'public service facility',
        'shop': 'retail store commercial',
        'office': 'business professional service',
        'tourism': 'hospitality accommodation',
        'craft': 'handcraft artisan production',
        'healthcare': 'medical health service',
        'leisure': 'recreation entertainment'
    }
    
    allowed_segments = {
        'shop': [str(i) for i in range(10, 70)], # Shops sell PRODUCTS (10-69)
        'craft': [str(i) for i in range(20, 40)] + ['72', '73', '80'], # Manufacturing/Repair
        'amenity': ['71', '76', '77', '78', '80', '83', '84', '85', '86', '90', '92', '93', '94'], # Public SERVICES (70-99)
        'office': ['71', '80', '82', '83', '84', '86'], # Professional SERVICES
        'tourism': ['90', '92'], # Travel/Lodging SERVICES
        'leisure': ['90', '92'], # Recreation SERVICES
        'healthcare': ['85'] # Medical SERVICES ONLY (not equipment)
    }
    
    valid_segments = allowed_segments.get(key, [str(i) for i in range(10, 99)])
    valid_indices = [i for i, c in enumerate(family_codes_list) if c[:2] in valid_segments]
    
    if not valid_indices:
        return None
        
    query_text = f"{val} {context.get(key, '')}".strip()
    query_embedding = model.encode([query_text])
    
    valid_embeddings = family_embeddings[valid_indices]
    similarities = cosine_similarity(query_embedding, valid_embeddings)[0]
    
    best_local_idx = int(np.argmax(similarities))
    best_score = float(similarities[best_local_idx])
    
    if best_score > 0.20:
        best_global_idx = valid_indices[best_local_idx]
        return family_codes_list[best_global_idx]
    return None

osm_to_family = {}
for tag in unique_tags:
    code = find_best_family(tag)
    if code:
        osm_to_family[tag] = code

print(f"Automatically mapped {len(osm_to_family)} OSM categories to UNSPSC Families.")

# ============================================================
# 3. GENERATE H3 RESOLUTION 9 GRID
# ============================================================
print("\n=== 3. Generating H3 Resolution 9 Grid ===")
S, W, N, E = 32.30, 51.05, 32.90, 51.80
bbox_poly = Polygon([(W, S), (E, S), (E, N), (W, N), (W, S)])
h3_shape = h3.geo_to_h3shape(bbox_poly)
h3_cells = h3.polygon_to_cells(h3_shape, 9)
print(f"Generated {len(h3_cells)} H3 Resolution 9 hexagons.")

# ============================================================
# 4. AGGREGATE OSM POIS TO H3 GRID
# ============================================================
print("\n=== 4. Aggregating OSM POIs to H3 Grid ===")
cell_labels = {cell: {} for cell in h3_cells}

for poi in pois:
    lat, lon = poi['lat'], poi['lon']
    cell = h3.latlng_to_cell(lat, lon, 9)
    
    if cell in cell_labels:
        osm_tag = poi['category']
        if osm_tag in osm_to_family:
            family_code = osm_to_family[osm_tag]
            cell_labels[cell][family_code] = cell_labels[cell].get(family_code, 0) + 1

labeled_cells_count = sum(1 for c in cell_labels.values() if len(c) > 0)
print(f"Found OSM evidence in {labeled_cells_count} out of {len(h3_cells)} hexagons.")

# ============================================================
# 5. SAVE GROUND TRUTH LABELS
# ============================================================
print("\n=== 5. Saving Ground Truth Labels ===")
rows = []
for cell, labels in cell_labels.items():
    if len(labels) > 0:
        for family_code, count in labels.items():
            rows.append({
                'h3_cell': cell,
                'family_code': family_code,
                'count': count
            })

df_labels = pd.DataFrame(rows)
df_labels.to_csv("data/OSM/h3_res9_labels.csv", index=False)

print(f"Saved {len(df_labels)} label entries to data/OSM/h3_res9_labels.csv")
print(f"Unique families found: {df_labels['family_code'].nunique()}")
print(f"\nTop 10 mapped families in dataset:")
top_families = df_labels['family_code'].value_counts().head(10)
for code, count in top_families.items():
    print(f"  {code} ({family_map.get(code, 'Unknown')}): {count}")
