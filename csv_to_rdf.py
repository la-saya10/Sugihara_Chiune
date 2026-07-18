import csv
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, FOAF, OWL

SUGIHARA = Namespace("http://example.org/sugihara/")
SCHEMA   = Namespace("https://schema.org/")
CRM      = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
WD       = Namespace("http://www.wikidata.org/entity/")

TYPE_CLASS = {
    "organization":  FOAF.Organization,
    "place":         SCHEMA.Place,
    "person":        FOAF.Person,
}

PROP = {
    "has title":           None,
    "has type":            RDF.type,        # ①コロンと末尾カンマを追加
    "is agency of":        SCHEMA.parentOrganization,
    "was located in":      SCHEMA.location,
    "was closed by":       CRM.P15_was_influenced_by,
    "was born in":         SCHEMA.birthPlace,
    "has publisher":       SCHEMA.publisher,  # ②SCHEMA:→SCHEMA.、末尾カンマを追加
    "has identifier":      OWL.sameAs,       # ③末尾カンマを追加
    "has author":          SCHEMA.author,    # 追加
    "has director":        SCHEMA.director,  # 追加
}

def uri(entity_id):
    slug = entity_id.strip().lower().replace(" ", "-")
    return SUGIHARA[slug]

g = Graph()
g.bind("sugihara", SUGIHARA)
g.bind("schema", SCHEMA)
g.bind("crm", CRM)
g.bind("foaf", FOAF)

with open("info.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if not row.get("subject") or not row["subject"].strip():
            continue

        subject   = row["subject"].strip()
        predicate = row["predicate"].strip()
        obj       = row["object"].strip()

        if predicate == "has type":
            g.add((uri(subject), RDF.type, TYPE_CLASS[obj]))

        elif predicate == "has title":
            g.add((uri(subject), SCHEMA.name, Literal(obj)))

        elif predicate == "has identifier": 
            g.add((uri(subject), OWL.sameAs, URIRef(WD[obj])))

        else:
            g.add((uri(subject), PROP[predicate], uri(obj)))

    

g.bind("wd", WD)
g.bind("owl", OWL)

g.serialize(destination="output_from_csv.ttl", format="turtle")
print(f"Transformation is successfully done! {len(g)} triples are made. Check output_from_csv.ttl")