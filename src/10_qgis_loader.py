from qgis.core import *

base = "/home/hmid/Projects/isfahan-wealth-flow-v4"

url = "type=xyz&url=file://" + base + "/tiles/{z}/{x}/{y}.png&zmin=9&zmax=15"
tiles = QgsRasterLayer(url, "OSM Isfahan local tiles", "wms")
QgsProject.instance().addMapLayer(tiles)

vl = QgsVectorLayer(base + "/data/OSM/v4_province_economic_nodes.geojson", "v4 Province Economic Nodes", "ogr")
QgsProject.instance().addMapLayer(vl)

field = "dominant_name"
vals = sorted(set(f[field] for f in vl.getFeatures()))
palette = ["#e6194b","#3cb44b","#ffe119","#4363d8","#f58231","#911eb4","#46f0f0","#f032e6","#bcf60c","#fabebe","#008080","#e6beff","#9a6324","#fffac8","#800000","#aaffc3","#808000","#ffd8b1","#000075","#808080"]

cats = []
for i, v in enumerate(vals):
    sym = QgsFillSymbol.createSimple({"color": palette[i % len(palette)], "outline_color": "#000000", "outline_width": "0.1"})
    cats.append(QgsRendererCategory(v, sym, str(v)))

renderer = QgsCategorizedSymbolRenderer(field, cats)
vl.setRenderer(renderer)
vl.setOpacity(0.65)
vl.triggerRepaint()

iface.setActiveLayer(vl)
iface.zoomToActiveLayer()
print("Layers loaded. Use the Identify tool to inspect.")
