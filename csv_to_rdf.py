import csv
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, FOAF, OWL

SUGIHARA = Namespace("http://example.org/sugihara/")
SCHEMA   = Namespace("https://schema.org/")
CRM      = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
WD       = Namespace("http://www.wikidata.org/entity/")

# CSVの"has type"の値 -> RDFクラス
TYPE_CLASS = {
    "organization":  FOAF.Organization,
    "place":         SCHEMA.Place,   
}

# CSVの述語 -> RDFプロパティ
PROP = {
    "has title":         None,  # 特別扱い(下のname処理を参照)
    "is agency of":       SCHEMA.parentOrganization,
    "hosted":             CRM.P7i_witnessed,
    "caused closure of":  CRM.P93_took_out_of_existence,
    "was born in":        SCHEMA.birthPlace,
    "has identifier":      OWL.sameAs
}

def uri(entity_id):
    return SUGIHARA[entity_id]  # 既存のXML由来のIDも新しいIDも、同じ名前空間で統一する

g = Graph()
g.bind("sugihara", SUGIHARA)
g.bind("schema", SCHEMA)
g.bind("crm", CRM)
g.bind("foaf", FOAF)

with open("info.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        # 空行(subjectが空)はスキップする
        if not row.get("subject") or not row["subject"].strip():
            continue

        subject   = row["subject"].strip()
        predicate = row["predicate"].strip()
        obj       = row["object"].strip()

        if predicate == "has type":
            g.add((uri(subject), RDF.type, TYPE_CLASS[obj]))

        elif predicate == "has title":
            g.add((uri(subject), FOAF.name, Literal(obj)))

        elif predicate == "has identifer":
            g.add((uri(subject), OWL.sameAs, URIRef(WD[obj])))

        else:
            g.add((uri(subject), PROP[predicate], uri(obj)))

g.bind("wd", WD)
g.bind("owl", OWL)

g.serialize(destination="output_from_csv.ttl", format="turtle")
print(f"Transformation is successfully done! {len(g)} triples are made. Check output_from_csv.ttl")
