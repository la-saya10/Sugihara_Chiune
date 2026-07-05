# ============================================================
# TEI -> RDF transformation
#
# Reads chiune_sugihara.xml and produces output.ttl in Turtle format.
# Uses only the classes and properties defined in the conceptual model.
#
# Run: python3 tei_to_rdf.py
# ============================================================

import xml.etree.ElementTree as ET
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, OWL, FOAF, SKOS

# ----- 1. Namespaces -----
CRM      = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
SCHEMA   = Namespace("https://schema.org/")
DCT      = Namespace("http://purl.org/dc/terms/")
WD       = Namespace("http://www.wikidata.org/entity/")
SUGIHARA = Namespace("http://example.org/sugihara/")

TEI    = "{http://www.tei-c.org/ns/1.0}"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"

# ----- 2. Conceptual model: entity id -> RDF class -----
TYPES = {
    "chiune":                FOAF.Person,
    "jan-zwartendijk":       FOAF.Person,
    "kaunas":                SCHEMA.City,
    "memorial-hall":         SCHEMA.Museum,
    "yad-vashem":            FOAF.Organization,
    "japanese-foreign-ministry": FOAF.Organization,
    "soviet-occupation":     CRM.E5_Event,
    "trans-siberian-railway": CRM.E25_Human_Made_Feature,
    "conspiracy-of-kindness": SCHEMA.Movie,
    "hero-of-the-holocaust": SCHEMA.Book,
    "righteous-among-nations": SKOS.Concept,
}

# ----- 3. Conceptual model: relation name -> RDF property -----
RELATIONS = {
    "servedIn":         SCHEMA.workLocation,
    "affectedBy":       CRM.P15_was_influenced_by,
    "enabledEscapeVia": CRM.P16_used_specific_object,
    "collaboratedWith": SCHEMA.colleague,
    "awardedTitle":     SCHEMA.award,
    "honoredBy":        SCHEMA.memberOf,
    "worksFor":         SCHEMA.worksFor,
    # reverse relations (passive -> active)
    "commemoratedAt":   SCHEMA.about,
    "isSubjectOf":      SCHEMA.about,
}
REVERSE = {"commemoratedAt", "isSubjectOf"}

# ----- 4. Parse TEI file -----
tree = ET.parse("chiune_sugihara.xml")
root = tree.getroot()

# ----- 5. Build graph -----
g = Graph()
g.bind("foaf",     FOAF)
g.bind("schema",   SCHEMA)
g.bind("crm",      CRM)
g.bind("skos",     SKOS)
g.bind("dcterms",  DCT)
g.bind("owl",      OWL)
g.bind("wd",       WD)
g.bind("sugihara", SUGIHARA)

# Helper: get the human-readable name of an entity element
def get_name(el):
    for tag in ("persName", "placeName", "orgName", "title",
                "head", "label", "catDesc"):
        child = el.find(TEI + tag)
        if child is not None and child.text:
            return child.text.strip()
    obj_name = el.find(f"{TEI}objectIdentifier/{TEI}objectName")
    if obj_name is not None and obj_name.text:
        return obj_name.text.strip()
    return el.get(XML_ID, "")

# Helper: get Wikidata QID URI from an element
def get_wikidata(el):
    idno = el.find(f"{TEI}idno[@type='Wikidata']")
    if idno is not None and idno.text:
        qid = idno.text.strip().rstrip("/").split("/")[-1]
        return URIRef(WD[qid])
    return None

# Walk all elements to find entities (those with xml:id in TYPES)
id_to_uri = {}

for el in root.iter():
    xml_id = el.get(XML_ID)
    if xml_id not in TYPES:
        continue

    uri = SUGIHARA[xml_id]
    id_to_uri[xml_id] = uri

    # rdf:type
    g.add((uri, RDF.type, TYPES[xml_id]))

    # name
    name = get_name(el)
    if name:
        prop = FOAF.name if TYPES[xml_id] in (FOAF.Person, FOAF.Organization) else SCHEMA.name
        g.add((uri, prop, Literal(name)))

    # owl:sameAs -> Wikidata
    wd = get_wikidata(el)
    if wd:
        g.add((uri, OWL.sameAs, wd))

    # owl:sameAs -> VIAF (persons only)
    viaf = el.find(f"{TEI}idno[@type='VIAF']")
    if viaf is not None and viaf.text:
        g.add((uri, OWL.sameAs, URIRef(viaf.text.strip())))

# ----- 6. Relations from listRelation -----
for rel in root.iter(TEI + "relation"):
    name    = rel.get("name")
    active  = rel.get("active",  "").lstrip("#")
    passive = rel.get("passive", "").lstrip("#")

    if name not in RELATIONS:
        continue
    if active not in id_to_uri or passive not in id_to_uri:
        continue

    prop = RELATIONS[name]
    if name in REVERSE:
        g.add((id_to_uri[passive], prop, id_to_uri[active]))
    else:
        g.add((id_to_uri[active], prop, id_to_uri[passive]))

# ----- 7. Extra triples from conceptual model -----

# World War II (indirect entity)
wwii = SUGIHARA["world-war-ii"]
g.add((wwii, RDF.type,   CRM.E5_Event))
g.add((wwii, RDFS.label, Literal("World War II", lang="en")))
g.add((wwii, OWL.sameAs, URIRef(WD["Q362"])))

# Soviet occupation -> isPartOf -> World War II
if "soviet-occupation" in id_to_uri:
    g.add((id_to_uri["soviet-occupation"], DCT.isPartOf, wwii))

# Soviet occupation -> took place at -> Kaunas
if "soviet-occupation" in id_to_uri and "kaunas" in id_to_uri:
    g.add((id_to_uri["soviet-occupation"],
           CRM.P7_took_place_at,
           id_to_uri["kaunas"]))

# Righteous Among the Nations -> inScheme -> Yad Vashem
if "righteous-among-nations" in id_to_uri and "yad-vashem" in id_to_uri:
    g.add((id_to_uri["righteous-among-nations"],
           SKOS.inScheme,
           id_to_uri["yad-vashem"]))

# ----- 8. Serialize -----
g.serialize(destination="output.ttl", format="turtle")
print("Transformation is successfully done! Check output.ttl")