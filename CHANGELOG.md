# Changelog

All notable changes to this project are documented in this file.
The format follows Keep a Changelog.

## [4.0.0] - 2026-09-27

First public release.

### Added
- Ten-script pipeline from raw OSM extract to knowledge graph.
- UNSPSC family ontology builder with 559 families from the UNDP Excel.
- Semantic category mapping with sentence-transformers.
- H3 resolution 9 grid over the study area with 44,842 hexagons.
- Hybrid multi-label model with 0.30 probability threshold.
- GeoNames supplement for rural anchor points.
- Fuseki knowledge graph injection with 52,984 triples.
- QGIS loader with categorized sector styling.
- Bundled assets: OSM extract, features, merged points, ontology, tiles archive.

### Changed
- One bounding box shared by all scripts.
- Negative sampling restricted to empty-land hexagons.

### Fixed
- Family code suffix ".0" removed at ontology build time.
- GeoJSON export keeps the geometry column.
- Duplicate rows from sjoin_nearest removed.

## [4.0.0-rc.1] - 2026-09-26

Pre-release validation build.
- Province-wide run exposed OSM point sparsity outside the metro core.
- Bounding box gaps between tiles, PBF and scripts identified and closed.
