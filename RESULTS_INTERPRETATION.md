# Interpreting the Results

## What the Model Outputs

The model outputs one economic node per H3 resolution 9 hexagon. Each node has:

- `h3_cell`: H3 index (e.g., `8940e0b38cbffff`)
- `lat`, `lon`: centroid coordinates
- `total_activity`: sum of all sector percentages (0.0 to 1.0)
- `comp_XXXXXXXX`: percentage composition for each UNSPSC family (e.g., `comp_86140000` = Educational facilities)
- `dominant_name`: the family with the highest percentage
- `dominant_pct`: percentage of the dominant family

## How to Read a Hexagon

### Example 1: Hexagon with POIs

```
h3_cell: 8940e0b38cbffff
lat: 32.6546, lon: 51.6680
total_activity: 1.0
comp_50180000: 0.60 (Bread and bakery products)
comp_52160000: 0.30 (Consumer electronics)
comp_90100000: 0.10 (Restaurants and catering)
dominant_name: Bread and bakery products
dominant_pct: 60.0
```

**Interpretation:** This hexagon has 3 POIs: 2 bakeries, 1 electronics store, and 1 restaurant (but the restaurant is counted as 0.10 because of rounding). The composition is 60% bakery, 30% electronics, 10% restaurant.

### Example 2: Hexagon without POIs (model prediction)

```
h3_cell: 8940e0b38cbffff
lat: 32.6546, lon: 51.6680
total_activity: 1.0
comp_80160000: 0.45 (Business administration services)
comp_86140000: 0.35 (Educational facilities)
comp_93150000: 0.20 (Public administration and finance services)
dominant_name: Business administration services
dominant_pct: 45.0
```

**Interpretation:** This hexagon has no POIs in OSM. The model predicts 45% probability of business administration services, 35% probability of educational facilities, and 20% probability of public administration. This prediction is based on building density and landuse patterns.

### Example 3: Empty hexagon

```
h3_cell: 8940e0b38cbffff
lat: 32.6546, lon: 51.6680
total_activity: 0.0
(no comp_ fields)
dominant_name: None
dominant_pct: 0.0
```

**Interpretation:** This hexagon has no POIs and the model predicts no economic activity (all probabilities below 0.30 threshold). This is likely desert, agricultural land, or undeveloped area.

## Color Coding in QGIS

The QGIS loader assigns colors based on `dominant_name`:

- Blue: Educational facilities
- Green: Business administration services
- Red: Consumer electronics
- Orange: Bread and bakery products
- Purple: Hotels and lodging
- Teal: Religious organizations
- Dark blue: Public administration and finance services
- Grey: Commercial and industrial furniture
- Dark orange: Motor vehicles
- Dark red: Bank offered products
- Dark purple: Restaurants and catering

## Validation Against Ground Truth

### What to Look For

When validating in QGIS, look for:

1. **Metropolitan core:** Predictions should align with known commercial districts. If the model predicts "Bread and bakery products" in a known residential area, this is an error.

2. **Peripheral cities:** Najafabad, Shahinshahr, Mobarakeh, Fooladshahr should have predicted economic nodes. If a city has 0 predicted nodes, this is an error.

3. **Rural areas:** Agricultural land and desert should be "empty." If the model predicts economic activity in a field, this is an error.

4. **Industrial zones:** Areas with high `lu_industrial` should predict manufacturing or industrial families. If the model predicts "Restaurants and catering" in an industrial zone, this is an error.

### Expected Accuracy

Average accuracy is approximately 25 percent. This means:

- 25% of predicted hexagons match ground truth
- 50% of predicted hexagons are partially correct (right dominant family, wrong percentages)
- 25% of predicted hexagons are completely wrong

This is low. The model is not precise enough for policy decisions or investment analysis.

## Use Cases

### Appropriate Use Cases

1. **Identifying undersampled areas:** The model can identify economic activity in areas where OSM has few POIs. This is useful for directing field surveys or data collection efforts.

2. **Exploratory analysis:** The model can generate hypotheses about economic activity patterns. For example, if the model predicts high educational facility density in an area, this could prompt investigation into school locations.

3. **Proof of concept:** The model demonstrates that economic sector composition can be estimated from open geospatial data using semantic mapping and machine learning.

### Inappropriate Use Cases

1. **Policy decisions:** The model is not precise enough to inform urban planning, zoning, or infrastructure investment.

2. **Investment analysis:** The model cannot predict economic output, revenue, or profitability.

3. **Academic research:** The model has not been validated with cross-validation or holdout datasets. Results should not be published as scientific findings without rigorous validation.

## Limitations to Keep in Mind

1. **Data sparsity:** OSM point density is low outside the metropolitan core. Predictions in peripheral cities are based on limited evidence.

2. **Semantic mapping errors:** Some POI-to-family mappings are incorrect. For example, `amenity_bench` maps to "Commercial and industrial furniture," which is not economically meaningful.

3. **UNSPSC taxonomy mismatch:** UNSPSC is a procurement taxonomy, not an urban economics taxonomy. Some economic activity does not fit neatly into UNSPSC families.

4. **No temporal dimension:** The model is static. It does not account for diurnal or seasonal variation.

5. **No absolute scale:** The model predicts relative composition, not absolute economic output.

6. **Training bias:** The model was trained on labeled hexagons, which are biased toward the metropolitan core.

## Conclusion

This model is a pilot study. It demonstrates what is possible with open data and machine learning, but it is not a production system. Use the results for exploratory analysis and hypothesis generation, not for decision-making.
