import xml.etree.ElementTree as ET
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, OWL, FOAF, SKOS, XSD

CRM      = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
SCHEMA   = Namespace("https://schema.org/")
WD       = Namespace("http://www.wikidata.org/entity/")
SUGIHARA = Namespace("http://example.org/sugihara/")
DCT      = Namespace("http://purl.org/dc/terms/")

TEI    = "{http://www.tei-c.org/ns/1.0}"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"

TYPES = {
    "chiune":                    FOAF.Person,
    "jan-zwartendijk":           FOAF.Person,
    "kaunas":                    SCHEMA.City,
    "memorial-hall":             SCHEMA.Museum,
    "yad-vashem":                FOAF.Organization,
    "japanese-foreign-ministry": FOAF.Organization,
    "soviet-occupation":         CRM.E5_Event,
    "transit-visa":              SCHEMA.Certification,
    "conspiracy-of-kindness":    SCHEMA.Movie,
    "hero-of-the-holocaust":     SCHEMA.Book,
    "righteous-among-nations":   SKOS.Concept,
}
NO_SAMEAS = {"transit-visa"}

RELATIONS = {
    "servedIn": SCHEMA.workLocation,
    "affectedBy": CRM.P15_was_influenced_by,
    "collaboratedWith": SCHEMA.colleague,
    "honoredBy": SCHEMA.recognizedBy,
    "worksFor": SCHEMA.worksFor,
    "isIssuedIn": SCHEMA.locationCreated,
    "wasRefusedBy": CRM.P15_was_influenced_by,
    "isDisplayedAt": CRM.P55_has_current_location,
    "wasIssuedDuring": DCT.temporal,
    "tookPlaceAt": CRM.P7_took_place_at,
    "issued": DCT.creator,
    "commemoratedAt": SCHEMA.about,
    "isSubjectOf": SCHEMA.about,
    "isCreatedBy": DCT.creator,
}
REVERSE = {"issued", "commemoratedAt", "isSubjectOf", "isCreatedBy"}

# note/desc/geo/pubPlaceはRDF化しない(除外リスト)
EXCLUDE = {"note", "desc", "geo", "pubPlace", "author", "publisher"}
HANDLED = {"idno", "persName", "placeName", "orgName", "title",
           "head", "catDesc", "objectIdentifier", "respStmt", "objectName"}

FIELD_MAP = {
    "birth":        SCHEMA.birthDate,
    "death":        SCHEMA.deathDate,
    "occupation":   SCHEMA.jobTitle,
    "date":         DCT.date,
    "date_founded": SCHEMA.foundingDate,
    "date_end":     SCHEMA.endDate,
    "date_opened":  SCHEMA.startDate,
    "term_genre":   SCHEMA.genre,
    "textLang":     SCHEMA.inLanguage,
    "country":      SCHEMA.addressCountry,
    "settlement":   SCHEMA.addressLocality,
}

DATE_FIELDS = {"birth", "death", "date", "date_founded", "date_end", "date_opened"}

def date_literal(value):
    #ハイフンが2個あればYYYY-MM-DD形式とみなしxsd:date、無ければxsd:gYear
    date_type = XSD.date if value.count("-") == 2 else XSD.gYear
    return Literal(value, datatype=date_type)

tree = ET.parse("chiune_sugihara.xml")
root = tree.getroot()

g = Graph()
g.bind("foaf", FOAF)
g.bind("schema", SCHEMA)
g.bind("crm", CRM)
g.bind("skos", SKOS)
g.bind("owl", OWL)
g.bind("wd", WD)
g.bind("sugihara", SUGIHARA)
g.bind("dcterms", DCT)

def get_name(el):
    for tag in ("persName", "placeName", "orgName", "title", "head", "catDesc"):
        child = el.find(TEI + tag)
        if child is not None and child.text:
            return child.text.strip()
    obj_name = el.find(f"{TEI}objectIdentifier/{TEI}objectName")
    if obj_name is not None and obj_name.text:
        return obj_name.text.strip()
    return el.get(XML_ID, "")

def get_wikidata(el):
    idno = el.find(f"{TEI}idno[@type='Wikidata']")
    if idno is not None and idno.text:
        qid = idno.text.strip().rstrip("/").split("/")[-1]
        return URIRef(WD[qid])
    return None





def collect_generic(el, uri):
   #note/desc以外の子タグを、ネストも含めて再帰的にすべてトリプル化する
    for child in el:
        tag = child.tag.split("}")[-1]
        if tag in EXCLUDE:
            continue

        if tag == "respStmt":
            continue

        if tag not in HANDLED:
            suffix = f"_{child.get('type')}" if child.get("type") else ""
            key = f"{tag}{suffix}"
            prop = FIELD_MAP.get(key, SUGIHARA[key])

            value = None
            if child.text and child.text.strip():
                value = child.text.strip()
            elif child.get("when"):
                value = child.get("when")

            if value:
                if key in DATE_FIELDS:
                    g.add((uri, prop, date_literal(value)))
                else:
                    g.add((uri, prop, Literal(value)))

        collect_generic(child, uri)




id_to_uri = {}
for el in root.iter():
    xml_id = el.get(XML_ID)
    if xml_id not in TYPES:
        continue
    uri = SUGIHARA[xml_id]
    id_to_uri[xml_id] = uri

    g.add((uri, RDF.type, TYPES[xml_id]))

    name = get_name(el)
    if name:
        prop = FOAF.name if TYPES[xml_id] in (FOAF.Person, FOAF.Organization) else SCHEMA.name
        g.add((uri, prop, Literal(name)))

    if xml_id not in NO_SAMEAS:
        wd = get_wikidata(el)
        if wd:
            g.add((uri, OWL.sameAs, wd))

    viaf = el.find(f"{TEI}idno[@type='VIAF']")
    if viaf is not None and viaf.text:
        g.add((uri, OWL.sameAs, URIRef(viaf.text.strip())))

    collect_generic(el, uri)

for rel in root.iter(TEI + "relation"):
    name = rel.get("name")
    active = rel.get("active", "").lstrip("#")
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


# -----  Extra triples  -----
if "transit-visa" in id_to_uri:
    g.add((id_to_uri["transit-visa"], CRM.P2_has_type, URIRef(WD["Q170404"])))
if "chiune" in id_to_uri:
    g.add((id_to_uri["chiune"], SCHEMA.award, Literal("Righteous Among the Nations")))
if "jan-zwartendijk" in id_to_uri:
    g.add((id_to_uri["jan-zwartendijk"], SCHEMA.award, Literal("Righteous Among the Nations")))

g.serialize(destination="output_from_tei.ttl", format="turtle")
print(f"Transformation is successfully finished! {len(g)} triples are made")