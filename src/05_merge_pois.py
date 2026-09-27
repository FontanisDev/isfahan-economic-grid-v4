import json
import os, subprocess
if not os.path.exists('data/geonames/IR.txt'):
    os.makedirs('data/geonames', exist_ok=True)
    print('Downloading GeoNames Iran...')
    subprocess.run(['wget', '-q', '-O', 'data/geonames/IR.zip', 'https://download.geonames.org/export/dump/IR.zip'], check=True)
    subprocess.run(['unzip', '-o', '-q', 'data/geonames/IR.zip', '-d', 'data/geonames/'], check=True)

all_pois = []
with open('data/OSM/isfahan_correct_pois.json', encoding='utf-8') as f:
    all_pois.extend(json.load(f))

# Add GeoNames for the correct extent
CODES = {
    'SCH': 'school', 'UNIV': 'university', 'HSP': 'hospital', 'MOSQ': 'mosque',
    'HTL': 'hotel', 'MKT': 'market', 'MALL': 'shopping mall', 'BANK': 'bank',
    'REST': 'restaurant', 'PS': 'post office', 'POL': 'police station',
    'LBR': 'library', 'MUS': 'museum', 'THTR': 'theater', 'STDM': 'stadium',
    'AIR': 'airport', 'RSTN': 'railway station', 'IND': 'industrial area',
    'MFG': 'factory', 'OIL': 'oil refinery', 'CH': 'church',
    'PPL': 'town center', 'PPLA': 'city center', 'PPLA2': 'city center',
    'PPLA3': 'town center', 'PPLA4': 'village center', 'PPLL': 'village center',
    'FRM': 'farm', 'PRK': 'park', 'RSRT': 'resort', 'GOVL': 'government office'
}

S, W, N, E = 32.30, 51.05, 32.90, 51.80

with open('data/geonames/IR.txt', encoding='utf-8') as f:
    for line in f:
        parts = line.rstrip('\n').split('\t')
        if len(parts) < 8:
            continue
        code = parts[7]
        if code in CODES:
            lat = float(parts[4])
            lon = float(parts[5])
            if S <= lat <= N and W <= lon <= E:
                all_pois.append({'lat': lat, 'lon': lon, 'category': f"geonames_{CODES[code]}"})

with open('data/OSM/pois_final_correct.json', 'w', encoding='utf-8') as f:
    json.dump(all_pois, f, ensure_ascii=False)

print(f"Merged {len(all_pois)} POIs (OSM + GeoNames)")
