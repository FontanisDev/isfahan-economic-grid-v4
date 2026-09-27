import h3
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon
from sklearn.ensemble import GradientBoostingClassifier
import warnings
warnings.filterwarnings('ignore')

print("=== 1. Loading Grid and Features ===")
S, W, N, E = 32.30, 51.05, 32.90, 51.80
bbox_poly = Polygon([(W, S), (E, S), (E, N), (W, N), (W, S)])
h3_shape = h3.geo_to_h3shape(bbox_poly)
h3_cells = list(h3.polygon_to_cells(h3_shape, 9))
print(f"Grid: {len(h3_cells)} H3 Res-9 cells.")

# Load dense features from previous run
osm_gdf = gpd.read_file("data/OSM/isfahan_correct_all.geojson")
osm_gdf = osm_gdf[osm_gdf.geometry.notna()].copy()

h3_polys = [Polygon([(p[1], p[0]) for p in h3.cell_to_boundary(c)]) for c in h3_cells]
grid_gdf = gpd.GeoDataFrame({'h3_cell': h3_cells}, geometry=h3_polys, crs="EPSG:4326")

utm_crs = "EPSG:32639"
grid_utm = grid_gdf.to_crs(utm_crs)
osm_utm = osm_gdf.to_crs(utm_crs)

buildings = osm_gdf[osm_gdf['building'].notna()].copy()
buildings['area_m2'] = osm_utm[osm_gdf['building'].notna()].geometry.area

landuse = osm_gdf[osm_gdf['landuse'].notna()].copy()
landuse['area_m2'] = osm_utm[osm_gdf['landuse'].notna()].geometry.area

print("Joining features to grid...")
bldg_join = gpd.sjoin(grid_gdf, buildings[['geometry', 'area_m2']], how="left", predicate="intersects")
bldg_agg = bldg_join.groupby('h3_cell').agg(
    building_count=('area_m2', 'count'),
    building_area=('area_m2', 'sum')
).reset_index().fillna(0)

lu_join = gpd.sjoin(grid_gdf, landuse[['geometry', 'landuse', 'area_m2']], how="left", predicate="intersects")
lu_agg = lu_join.groupby(['h3_cell', 'landuse'])['area_m2'].sum().unstack(fill_value=0).reset_index()
lu_agg.columns = [f"lu_{c}" if c != 'h3_cell' else c for c in lu_agg.columns]

features_df = grid_gdf[['h3_cell']].merge(bldg_agg, on='h3_cell', how='left')
features_df = features_df.merge(lu_agg, on='h3_cell', how='left')
features_df = features_df.fillna(0)

lat_lon = [h3.cell_to_latlng(c) for c in features_df['h3_cell']]
features_df['lat'] = [x[0] for x in lat_lon]
features_df['lon'] = [x[1] for x in lat_lon]
center_lat, center_lon = 32.6546, 51.6680
features_df['dist_to_center'] = np.sqrt((features_df['lat'] - center_lat)**2 + (features_df['lon'] - center_lon)**2)

print(f"Features extracted for {len(features_df)} cells.")

print("\n=== 2. Loading Ground Truth Labels ===")
labels_df = pd.read_csv("data/OSM/h3_res9_labels.csv")
multi_hot = labels_df.pivot_table(index='h3_cell', columns='family_code', values='count', fill_value=0, aggfunc='sum')
multi_hot = (multi_hot > 0).astype(int)

# Also keep raw counts for composition
raw_counts = labels_df.pivot_table(index='h3_cell', columns='family_code', values='count', fill_value=0, aggfunc='sum')

labeled_cells = set(multi_hot.index)
print(f"Labeled cells: {len(labeled_cells)}")

print("\n=== 3. Training Model for Unlabeled Cells ===")
# Training: labeled cells as positive, random unlabeled as negative
positive_idx = features_df[features_df['h3_cell'].isin(labeled_cells)].index
negative_pool = features_df[(~features_df['h3_cell'].isin(labeled_cells)) & (features_df['building_count'] == 0)].index
negative_idx = negative_pool.to_series().sample(n=min(5000, len(negative_pool)), random_state=42).index

train_idx = positive_idx.append(negative_idx)
train_X = features_df.loc[train_idx].drop(columns=['h3_cell', 'lat', 'lon', 'dist_to_center']).to_numpy(dtype=np.float32)

# Build labels: positive cells get their multi-hot, negative cells get all zeros
train_y_pos = multi_hot.loc[features_df.loc[positive_idx, 'h3_cell']].to_numpy(dtype=np.int32)
train_y_neg = np.zeros((len(negative_idx), multi_hot.shape[1]), dtype=np.int32)
train_y = np.vstack([train_y_pos, train_y_neg])

print(f"Training: {len(train_y_pos)} positive + {len(train_y_neg)} negative = {len(train_y)} total")

# Train one model per family (only for families with enough samples)
family_cols = multi_hot.columns.tolist()
models = {}
THRESHOLD = 0.30

for i, fam in enumerate(family_cols):
    y_col = train_y[:, i]
    if y_col.sum() < 10:
        continue
    clf = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42, subsample=0.8)
    clf.fit(train_X, y_col)
    models[fam] = clf

print(f"Trained {len(models)} family models.")

print("\n=== 4. Hybrid Prediction ===")
# For ALL cells, predict probabilities
X_all = features_df.drop(columns=['h3_cell', 'lat', 'lon', 'dist_to_center']).to_numpy(dtype=np.float32)

prob_matrix = np.zeros((len(features_df), len(family_cols)))
for i, fam in enumerate(family_cols):
    if fam in models:
        prob_matrix[:, i] = models[fam].predict_proba(X_all)[:, 1]

# HYBRID LOGIC:
# - For cells WITH POIs: use actual OSM counts as composition
# - For cells WITHOUT POIs: use model predictions with threshold
final_composition = np.zeros_like(prob_matrix)

for idx, row in features_df.iterrows():
    cell = row['h3_cell']
    pos = features_df.index.get_loc(idx)
    
    if cell in labeled_cells:
        # Use ground truth: normalize actual POI counts
        counts = raw_counts.loc[cell].to_numpy(dtype=np.float64)
        total = counts.sum()
        if total > 0:
            final_composition[pos] = counts / total
    else:
        # Use model prediction with threshold
        probs = prob_matrix[pos]
        probs[probs < THRESHOLD] = 0
        total = probs.sum()
        if total > 0:
            final_composition[pos] = probs / total

# Save
comp_df = pd.DataFrame(final_composition, columns=[f'comp_{c}' for c in family_cols])
prob_df = pd.DataFrame(prob_matrix, columns=[f'prob_{c}' for c in family_cols])

out_df = features_df[['h3_cell', 'lat', 'lon']].copy()
out_df = pd.concat([out_df, comp_df, prob_df], axis=1)
out_df.to_csv("data/OSM/h3_res9_final_predictions.csv", index=False)

# Stats
active_cells = (final_composition.sum(axis=1) > 0).sum()
print(f"\nCells with economic activity: {active_cells} / {len(features_df)}")
print(f"Cells labeled 'empty': {len(features_df) - active_cells}")

print("\nTop 10 families by expected active cells (threshold > 0.3):")
for i, fam in enumerate(family_cols):
    active = (prob_matrix[:, i] > THRESHOLD).sum()
    if active > 0:
        print(f"  {fam}: {active} cells")

# Sort by activity
family_activity = [(fam, (prob_matrix[:, i] > THRESHOLD).sum()) for i, fam in enumerate(family_cols)]
family_activity.sort(key=lambda x: x[1], reverse=True)
print("\nTop 10:")
for fam, count in family_activity[:10]:
    print(f"  {fam}: {count} cells")
