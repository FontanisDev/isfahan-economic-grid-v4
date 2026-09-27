# RELEASE NOTES v4

Release date: 2026-09-27
Project: Isfahan Wealth Flow
Version: 4.0

## Scope

Study area bounding box: S=32.30, W=51.05, N=32.90, E=51.80
West limit: Rezvanshahr
East limit: Shahid Beheshti Airport
North limit: Shahinshahr
South limit: Mobarakeh
Grid: H3 resolution 9, 44,842 hexagons

## Data Sources

1. OpenStreetMap extract via Overpass API (script 02)
2. GeoNames Iran dump, automatic download (script 05)
3. UNDP UNSPSC version 26.08.01 (script 01)
4. Local OSM raster tiles, bundled asset, zoom 9 to 15

## Pipeline

Ten scripts in src/ run in numbered order.
Script 01 builds the UNSPSC family ontology.
Scripts 02 to 05 prepare OSM and GeoNames inputs.
Script 06 maps categories to UNSPSC and builds labels.
Script 07 trains models and predicts composition.
Scripts 08 and 09 export GeoJSON and inject the knowledge graph.
Script 10 loads results in QGIS.

## Model

Hybrid multi-label design.
Labeled hexagons keep their measured POI composition.
Unlabeled hexagons use gradient boosting probabilities.
Prediction threshold: 0.30
Negative samples: 5,000 empty-land hexagons
Trained family models: 68

## Results

Active economic nodes: 6,416
Labeled hexagons: 3,696
Knowledge graph triples: 52,984
City coverage: Isfahan 3,016, Najafabad 267, Shahinshahr 228, Mobarakeh 212, Fooladshahr 137
Top families: Educational facilities 1,043, Clubs 1,013, Bread and bakery 762, Business administration 633, Hotels and lodging 598

## Bundled Assets

- data/OSM/isfahan_correct.pbf
- data/OSM/isfahan_correct_all.geojson
- data/OSM/isfahan_correct_pois.json
- data/OSM/pois_final_correct.json
- ontology/unspsc_full.ttl
- tiles/ (zoom 9 to 15)

## Validation

Open QGIS and run script 10 in the Python console.
Use the Identify tool on any hexagon.
Query the Fuseki dataset isfahan_wealth with SPARQL.

## Limitations

OSM point density is low outside the metropolitan core.
GeoNames supplies rural anchor points.
Tiles at zoom 12 to 15 cover the metropolitan core only.
UNSPSC is a procurement taxonomy, so service mappings are approximate.

## Changes From v3

v3 produced one wealth index on a 0.01 degree grid.
v4 produces multi-sector composition per H3 hexagon.
v4 adds semantic UNSPSC mapping with sentence-transformers.
v4 adds hybrid machine learning for unlabeled hexagons.
v4 adds a knowledge graph in Apache Fuseki.

## Release Assets

The following files are attached to this release:

1. `unspsc-english-v260801.1.xlsx` (14 MB) - Official UNSPSC code list
2. `tiles.zip` (300 MB) - OSM raster tiles for local rendering
3. `unspsc_full.ttl` (57 KB) - Derived UNSPSC family ontology
4. `v4-QGIS.qgz` (15 KB) - QGIS project with pre-configured styling

Download these files and place them in the locations specified in README.md.
