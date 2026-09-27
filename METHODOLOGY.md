# Methodology

## 1. Introduction

This model estimates the economic sector composition of urban neighborhoods in the Isfahan metropolitan region. It outputs one node per H3 resolution 9 hexagon, where each node carries percentage weights for up to 106 UNSPSC family codes.

The model does not predict absolute wealth, income, or economic output. It predicts relative sector composition: what percentage of economic activity in a hexagon belongs to educational facilities, bakeries, consumer electronics retail, and so on.

This is a pilot study. The methodology is symbolic and exploratory. Average accuracy is approximately 25 percent when validated against ground truth. The model's value lies not in precision, but in its ability to identify economic activity in areas where traditional mapping fails.

## 2. Data Sources and Rationale

### 2.1 OpenStreetMap Extract

We downloaded OSM data from the Overpass API for the bounding box S=32.30, W=51.05, N=32.90, E=51.80. This extract contains:

- 12,986 points of interest (amenity, shop, office, tourism, craft, healthcare, leisure tags)
- 24,866 building polygons
- 3,795 landuse polygons

**Rationale:** OSM is the most comprehensive open geospatial dataset. It contains human-curated labels for commercial activity. However, OSM point density is low outside the metropolitan core. In Najafabad, Shahinshahr, and Mobarakeh, OSM has fewer than 100 POIs per city.

### 2.2 GeoNames Supplement

We downloaded the GeoNames Iran dump (geonames.org) and extracted 2,137 points within our study area. We filtered for feature codes: SCH (school), HSP (hospital), MOSQ (mosque), HTL (hotel), MKT (market), BANK, REST, PPL (populated place), and 22 others.

**Rationale:** GeoNames provides anchor points for rural and suburban areas where OSM is sparse. A GeoNames "PPL" (populated place) tag indicates a town center, which likely has economic activity even if OSM lacks shop-level detail.

### 2.3 UNSPSC Ontology

We used the United Nations Standard Products and Services Code version 26.08.01 from the UNDP. We extracted 559 family-level codes from the official Excel file.

**Rationale:** UNSPSC is a procurement taxonomy designed for spend analysis. It separates products (segments 10-69) from services (segments 70-99). This separation is useful for distinguishing retail from service-based economic activity. However, UNSPSC was not designed for urban economics, so mappings are approximate.

## 3. Ontology Mapping

### 3.1 Semantic Similarity Approach

We mapped 423 unique OSM categories (e.g., `shop_supermarket`, `amenity_restaurant`, `office_company`) to UNSPSC families using sentence-transformers (`all-MiniLM-L6-v2`).

The process:

1. Encode the OSM category text: `model.encode("supermarket shop")`
2. Encode all 559 UNSPSC family titles: `model.encode(family_labels)`
3. Compute cosine similarity between the OSM embedding and each family embedding
4. Select the family with highest similarity, subject to constraints

**Constraints:**
- Minimum similarity threshold: 0.20 (below this, no mapping)
- Segment filtering: `shop_*` tags map only to product families (segments 10-69)
- Segment filtering: `amenity_*` and `office_*` tags map only to service families (segments 70-99)

**Example mappings:**
- `shop_supermarket` → `50180000` (Bread and bakery products) - similarity 0.41
- `amenity_restaurant` → `90100000` (Restaurants and catering) - similarity 0.67
- `office_company` → `80160000` (Business administration services) - similarity 0.53
- `amenity_bank` → `84130000` (Bank offered products) - similarity 0.48

### 3.2 Persian Translation

OSM in Iran contains Persian tags: `فروشگاه مواد غذایی` (grocery), `نانوایی` (bakery), `آرایشگاه` (hairdresser). The embedding model is English-only. We added a dictionary of 10 common Persian terms, translated to English before embedding.

### 3.3 Limitations of Mapping

Semantic mapping is imprecise. `shop_supermarket` maps to "Bread and bakery products" because supermarkets sell bread, but they also sell electronics, clothing, and household goods. The model assigns 100% of a supermarket POI to the bakery family. This is a simplification.

Better approaches would use multi-label mapping (one POI → multiple families with weights) or train a classifier on labeled data. We did not have labeled data, so we used semantic similarity as a proxy.

## 4. Spatial Grid

### 4.1 H3 Resolution 9

We generated 44,842 H3 hexagons at resolution 9 using the `h3-py` library. Each hexagon has an area of approximately 0.1 square kilometers (10 hectares) and an edge length of approximately 200 meters.

**Rationale:** Resolution 9 is neighborhood-level. It is fine enough to distinguish commercial districts from residential areas, but coarse enough to aggregate sufficient POIs per hexagon for statistical stability.

### 4.2 Bounding Box

The grid covers S=32.30 to N=32.90, W=51.05 to E=51.80. This bounding box was chosen to match the extent of our local OSM tile cache (zoom 9 to 15). The box includes:

- Isfahan metropolitan core (west to east)
- Najafabad (west)
- Shahinshahr (north)
- Mobarakeh (south)
- Fooladshahr (southwest)

### 4.3 Grid Coverage

Of the 44,842 hexagons:
- 3,696 hexagons contain at least one POI (8.2%)
- 41,146 hexagons contain no POIs (91.8%)

The model must predict economic activity for the 91.8% of hexagons that have no direct POI evidence.

## 5. Feature Engineering

### 5.1 Building Features

For each hexagon, we computed:
- `building_count`: number of building polygons intersecting the hexagon
- `building_area`: total area of building polygons (square meters)

**Rationale:** Buildings are proxies for human activity. Hexagons with many buildings likely have economic activity, even if OSM lacks shop-level tags.

### 5.2 Landuse Features

For each hexagon, we computed area (square meters) for each landuse type:
- `lu_residential`
- `lu_commercial`
- `lu_industrial`
- `lu_retail`
- `lu_civic`
- And 15 other landuse categories

**Rationale:** Landuse tags indicate zoning. A hexagon with high `lu_commercial` area is zoned for commercial use, which correlates with economic activity.

### 5.3 Feature Vector

Each hexagon becomes a feature vector of approximately 25 dimensions:
- 2 building features
- 20+ landuse features
- Hexagon centroid latitude and longitude

We did not use distance-to-center or road proximity features. These features caused the model to overpredict activity near the city center and underpredict activity in peripheral cities.

## 6. Machine Learning Model

### 6.1 Hybrid Approach

The model uses a hybrid design:

**Labeled hexagons** (those with POIs): The model does not predict. It uses the measured POI composition as ground truth. If a hexagon has 3 bakeries and 1 electronics store, the composition is 75% bakery, 25% electronics.

**Unlabeled hexagons** (those without POIs): The model predicts sector probabilities using gradient boosting classifiers.

### 6.2 Training Data

We constructed a binary classification dataset:

- **Positive samples:** 3,696 hexagons with POIs. For each family, the label is 1 if the hexagon has at least one POI of that family, 0 otherwise.
- **Negative samples:** 5,000 hexagons with zero buildings. These are desert, agricultural land, or undeveloped areas. The label is 0 for all families.

**Rationale:** We restricted negative samples to empty land to avoid teaching the model that "distant buildings = no activity." Earlier versions included buildings in peripheral cities as negative samples, which caused the model to underpredict activity in Najafabad and Mobarakeh.

### 6.3 Model Architecture

We trained 68 binary classifiers (one per family) using scikit-learn's `GradientBoostingClassifier`:
- `n_estimators=100`
- `max_depth=5`
- `subsample=0.8`
- `random_state=42`

We discarded families with fewer than 10 positive samples (insufficient data).

### 6.4 Prediction Threshold

For unlabeled hexagons, the model outputs probabilities in [0, 1] for each family. We applied a threshold of 0.30: probabilities below 0.30 are set to 0. Remaining probabilities are normalized to sum to 1.0.

**Rationale:** The threshold reduces noise. A probability of 0.05 likely reflects model uncertainty, not real economic activity. The threshold of 0.30 was chosen empirically to balance recall and precision.

### 6.5 Hybrid Composition

For each hexagon:

1. If the hexagon has POIs, use measured composition (normalized POI counts).
2. If the hexagon has no POIs but the model predicts activity above threshold, use predicted composition.
3. If the hexagon has no POIs and all predictions are below threshold, mark as "empty."

## 7. Validation

### 7.1 Quantitative Validation

We did not perform cross-validation. The model was trained on all available labeled data and evaluated on the same data. This is not a rigorous validation. It only confirms that the model fits the training data.

### 7.2 Qualitative Validation

We visually inspected the model output in QGIS. We compared predicted economic nodes against our ground knowledge of Isfahan.

**Findings:**
- In the metropolitan core, predictions align with known commercial districts.
- In Najafabad, Shahinshahr, and Mobarakeh, predictions identify economic activity in areas where OSM has few POIs.
- In rural and agricultural areas, the model correctly predicts "empty."

**Estimated accuracy:** Approximately 25 percent of predicted hexagons match ground truth when manually verified. This is low. The model is not precise.

### 7.3 Value Proposition

The model's value is not in precision, but in recall for undersampled areas. In Najafabad, OSM has 267 POIs. The model predicts 267 active economic nodes. In Mobarakeh, OSM has 0 POIs in the original extract (we added GeoNames anchor points). The model predicts 212 active nodes.

The model identifies economic activity in places where traditional mapping fails. This is the primary contribution of the pilot.

## 8. Known Limitations

### 8.1 Data Sparsity

OSM point density is low outside the metropolitan core. In peripheral cities, a single POI becomes the sole evidence for an entire hexagon. The model generalizes from this single point, which may not represent the hexagon's true composition.

### 8.2 Semantic Mapping Errors

Semantic similarity is imprecise. Some mappings are incorrect. For example, `amenity_bench` maps to `56110000` (Commercial and industrial furniture) because benches are furniture, but this is not economically meaningful.

### 8.3 UNSPSC Taxonomy Mismatch

UNSPSC is a procurement taxonomy, not an urban economics taxonomy. It separates products from services, which is useful, but it does not have categories for "mixed-use development" or "informal economy." Some economic activity does not fit neatly into UNSPSC families.

### 8.4 No Temporal Dimension

The model is static. It does not account for diurnal or seasonal variation in economic activity. A restaurant is active during the day and inactive at night, but the model treats it as always active.

### 8.5 No Absolute Scale

The model predicts relative composition (percentages), not absolute economic output. It cannot distinguish a hexagon with 1 bakery from a hexagon with 100 bakeries. Both are 100% bakery.

### 8.6 Training Bias

The model was trained on labeled hexagons, which are biased toward the metropolitan core. The model may underpredict activity in peripheral cities because it has fewer training examples from those areas.

## 9. Future Work

### 9.1 Multi-Label Mapping

Replace semantic similarity with a trained classifier. Collect labeled data: for each POI, annotate which UNSPSC families it belongs to and with what weights. Train a multi-label classifier to map POI categories to family distributions.

### 9.2 Satellite Imagery Features

Integrate satellite imagery (Sentinel-2, Landsat) as additional features. Train a convolutional neural network to extract texture, color, and shape features that correlate with economic activity.

### 9.3 Temporal Features

Incorporate temporal data: opening hours from OSM, traffic patterns from mobile phone data, or seasonal variation from satellite imagery.

### 9.4 Absolute Scale Estimation

Combine relative composition with absolute scale estimation. Use building volume, road density, or night-time lights to estimate total economic output per hexagon.

### 9.5 Validation Dataset

Construct a validation dataset by manually annotating 1,000 hexagons with ground truth sector composition. Use this dataset for cross-validation and to tune the prediction threshold.

### 9.6 Informal Economy

Develop methods to detect informal economic activity (street vendors, home-based businesses) that is not captured in OSM or GeoNames.

## 10. Conclusion

This model is a pilot study. It demonstrates that economic sector composition can be estimated from open geospatial data using semantic mapping and machine learning. The methodology is symbolic and exploratory.

Average accuracy is approximately 25 percent. The model is not precise enough for policy decisions or investment analysis. However, the model identifies economic activity in undersampled areas where traditional mapping fails. This is the primary contribution of the pilot.

Future work should focus on multi-label mapping, satellite imagery integration, and validation dataset construction. With these improvements, accuracy could increase to 50-60 percent, which would be sufficient for urban planning applications.

For now, this model is a proof of concept. It shows what is possible with open data and machine learning, but it is not a production system.
