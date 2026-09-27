# Isfahan Wealth Flow v4

Economic sector composition model for the Isfahan metropolitan region.
The model outputs one economic node per H3 resolution 9 hexagon.
Each node carries a percentage composition of UNSPSC families.

## Study Area

Bounding box: S=32.30, W=51.05, N=32.90, E=51.80
West edge: Rezvanshahr
East edge: Shahid Beheshti Airport
North edge: Shahinshahr
South edge: Mobarakeh

## Prerequisites

1. Python 3.10 or newer
2. Apache Jena Fuseki running on port 3030 with dataset `isfahan_wealth`
3. QGIS for visual validation
4. No manual data download

The release bundle includes all required data assets.
The UNSPSC Excel is only needed to rebuild the ontology from scratch.

Start Fuseki:

    docker run -d -p 3030:3030 -e ADMIN_PASSWORD=admin atomgraph/fuseki --enable-write --dataset /isfahan_wealth

## Installation

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

## Pipeline

Run the scripts in this exact order:

    python3 src/01_build_ontology.py
    python3 src/02_download_osm.py
    python3 src/03_extract_features.py
    python3 src/04_extract_pois.py
    python3 src/05_merge_pois.py
    python3 src/06_build_grid_labels.py
    python3 src/07_train_predict.py
    python3 src/08_export_inject_kg.py
    python3 src/09_add_sector_names.py

Script 02 downloads OSM data from the Overpass API.
Script 05 downloads GeoNames Iran automatically.
Scripts 06 and 07 perform mapping, training and prediction.
Script 08 exports GeoJSON and injects the knowledge graph.
Script 09 adds readable sector names to the GeoJSON.

## Outputs

- data/OSM/h3_res9_labels.csv
- data/OSM/h3_res9_final_predictions.csv
- data/OSM/v4_province_economic_nodes.geojson
- ontology/unspsc_full.ttl

## Visual Validation

Open QGIS.
Open the Python console.
Run:

    exec(open('src/10_qgis_loader.py').read())

Use the Identify tool to inspect any hexagon.

## Method Summary

1. OSM and GeoNames points become ground truth labels.
2. A sentence-transformers model maps point categories to UNSPSC families.
3. Building and landuse polygons become dense features per hexagon.
4. Gradient boosting models predict family probabilities for unlabeled hexagons.
5. Labeled hexagons keep their measured composition.
6. Unlabeled hexagons keep predictions above 0.30 probability.

## License

State your license here before publication.

## Bundled Assets

- data/OSM/isfahan_correct.pbf: OSM extract for the study area
- data/OSM/isfahan_correct_all.geojson: building and landuse polygons
- data/OSM/isfahan_correct_pois.json: OSM points of interest
- data/OSM/pois_final_correct.json: merged OSM and GeoNames points
- ontology/unspsc_full.ttl: UNSPSC family ontology, 559 families
- tiles/: local OSM raster tiles, zoom 9 to 15 (ships as tiles.zip in GitHub Releases)

Scripts skip downloads when assets already exist.

## Download Large Assets

The following files are available in the GitHub Release assets:

- `unspsc-english-v260801.1.xlsx` - Official UNSPSC Excel file
- `tiles.zip` - Local OSM raster tiles (zoom 9-15)
- `unspsc_full.ttl` - Complete UNSPSC ontology
- `v4-QGIS.qgz` - Pre-configured QGIS project

Download from: [Releases page](https://github.com/FontanisDev/isfahan-economic-grid-v4/releases)

After downloading, place them in:
- `data/unspsc-english-v260801.1.xlsx`
- `ontology/unspsc_full.ttl`
- Unzip `tiles.zip` to get `tiles/` folder
- `v4-QGIS.qgz` (root directory)

## Additional Large Data Files

These files are in the GitHub Release assets:

- `isfahan_correct.pbf` - OSM extract for the study area
- `isfahan_correct_all.geojson` - Building and landuse polygons

Download from: [Releases page](https://github.com/FontanisDev/isfahan-economic-grid-v4/releases)

Place them in `data/OSM/` after download.
