from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL, FOAF, SKOS, XSD


# -----  Namespaces  -----
CRM    = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
SCHEMA = Namespace("https://schema.org/")
SKOS   = Namespace("http://www.w3.org/2004/02/skos/core#")
DCT    = Namespace("http://purl.org/dc/terms/")
FRBR   = Namespace("http://purl.org/vocab/frbr/core#")
WDT    = Namespace("http://www.wikidata.org/prop/direct/")
WD     = Namespace("http://www.wikidata.org/entity/")
ns = {"tei": "http://www.tei-c.org/ns/1.0"}
EX = Namespace("http://example.org/relation/")


# ① TEIファイルを読み込む(前回と同じ)
tree = etree.parse("mini_example.xml")

# ③ 空のRDFグラフ(トリプルを入れる箱)を用意
g = Graph()

# ④ TEI内の<person>要素をすべて取り出し、Wikidata IDとxml:idを対応付ける辞書を作る


#  Person
id_to_uri = {}
for person in tree.findall(".//tei:person", ns):
    xml_id = person.get("{http://www.w3.org/XML/1998/namespace}id")
    wikidata_url = person.find("tei:idno[@type='Wikidata']", ns).text
    id_to_uri[xml_id] = URIRef(wikidata_url)

# Place
for place in tree.findall(".//tei:place", ns):
    xml_id = place.get("{http://www.w3.org/XML/1998/namespace}id")
    wikidata_url = place.find("tei:idno[@type='Wikidata']", ns).text
    id_to_uri[xml_id] = URIRef(wikidata_url)



# Organization
for organization in tree.findall(".//tei:orgName", ns):
    xml_id = organization.get("{http://www.w3.org/XML/1998/namespace}id")
    wikidata_url = organization.find("tei:idno[@type='Wikidata']", ns).text
    id_to_uri[xml_id] = URIRef(wikidata_url)


# Bibl
for bibl in tree.findall(".//tei:bibl", ns):
    xml_id = bibl.get("{http://www.w3.org/XML/1998/namespace}id")

    idno_elem = bibl.find("tei:idno[@type='Wikidata']", ns)

    if idno_elem is not None:
        # Wikidataがあれば、そのまま使う
        id_to_uri[xml_id] = URIRef(idno_elem.text)
    else:
        # なければ(=この本の場合)、OCLCから組み立てる
        oclc_elem = bibl.find("tei:idno[@type='OCLC']", ns)
        oclc_number = oclc_elem.text
        id_to_uri[xml_id] = URIRef(f"https://www.worldcat.org/oclc/{oclc_number}")


# Object
for object in tree.findall(".//tei:rs[@type='event'] | tei:rs[@type='infrastructure'] | tei:rs[@type='concept']", ns):
    xml_id = place.get("{http://www.w3.org/XML/1998/namespace}id")
    wikidata_url = place.find("tei:idno[@type='Wikidata']", ns).text
    id_to_uri[xml_id] = URIRef(wikidata_url)
