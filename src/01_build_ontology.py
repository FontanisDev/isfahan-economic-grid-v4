import pandas as pd
import os
if os.path.exists("ontology/unspsc_full.ttl"):
    print("Ontology already exists. Skipping build.")
    raise SystemExit(0)
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, SKOS

print("Reading official UNSPSC Excel with correct header (row 12)...")
df = pd.read_excel("data/unspsc-english-v260801.1.xlsx", header=12)

# In the official UNDP Excel, Family code is usually column index 5 and title is 6
# Let's dynamically find them to be safe, or just use iloc
# We know from the header row: Segment, Seg Title, Seg Def, Family, Fam Title...
family_df = df.iloc[:, [5, 6]].copy()
family_df.columns = ['Family_Code', 'Family_Title']

family_df = family_df.dropna(subset=['Family_Code'])
family_df['Family_Code'] = family_df['Family_Code'].astype(str).str.replace('.0', '', regex=False).str.zfill(8)
family_df = family_df.drop_duplicates(subset=['Family_Code'])

print(f"Extracted {len(family_df)} unique Families from official UNDP dataset.")
print("\nSample of extracted families (checking for services like 70-99):")
print(family_df[family_df['Family_Code'].str.startswith(('71', '80', '84', '85', '90'))].head(10))

print("\nBuilding complete Turtle (TTL) Ontology...")
UNSPSC = Namespace("http://ontoview.org/schema/unspsc/1/")
g = Graph()
g.bind("skos", SKOS)
g.bind("unspsc", UNSPSC)

for _, row in family_df.iterrows():
    code = row['Family_Code']
    title = row['Family_Title']
    uri = UNSPSC[f"Family_{code}"]
    g.add((uri, RDF.type, SKOS.Concept))
    g.add((uri, SKOS.prefLabel, Literal(str(title), lang='en')))

out_path = "ontology/unspsc_full.ttl"
g.serialize(destination=out_path, format="turtle")
print(f"SUCCESS: Saved complete ontology ({len(family_df)} families) to {out_path}")
