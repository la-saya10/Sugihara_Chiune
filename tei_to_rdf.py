from lxml import etree
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL, FOAF,  XSD


# -----  Namespaces  -----
CRM    = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
SCHEMA = Namespace("https://schema.org/")
SKOS   = Namespace("http://www.w3.org/2004/02/skos/core#")
DCT    = Namespace("http://purl.org/dc/terms/")
FRBR   = Namespace("http://purl.org/vocab/frbr/core#")
WDT    = Namespace("http://www.wikidata.org/prop/direct/")
WD     = Namespace("http://www.wikidata.org/entity/")
ns     = {"tei": "http://www.tei-c.org/ns/1.0"}
EX     = Namespace("http://example.org/relation/")


# ① TEIファイルを読み込む(前回と同じ)
tree = etree.parse("chiune_sugihara.xml")

# ③ 空のRDFグラフ(トリプルを入れる箱)を用意
g = Graph()


# ④ TEI内の要素をすべて取り出し、Wikidata IDとxml:idを対応付ける辞書を作る
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
for organization in tree.findall(".//tei:org", ns):
    xml_id = organization.get("{http://www.w3.org/XML/1998/namespace}id")
    wikidata_url = organization.find("tei:idno[@type='Wikidata']", ns).text
    id_to_uri[xml_id] = URIRef(wikidata_url)


# Bibl
for bibl in tree.findall(".//tei:listBibl/tei:bibl", ns):
    xml_id = bibl.get("{http://www.w3.org/XML/1998/namespace}id")

    # ★ xml:idが無い(RDF化する対象ではない)場合はスキップ
    if xml_id is None:
        continue

    idno_elem = bibl.find("tei:idno[@type='Wikidata']", ns)

    if idno_elem is not None:
        # Wikidataがあれば、そのまま使う
        id_to_uri[xml_id] = URIRef(idno_elem.text)
    else:
        # なければ、OCLCから組み立てる
        oclc_elem = bibl.find("tei:idno[@type='OCLC']", ns)
        oclc_number = oclc_elem.text
        id_to_uri[xml_id] = URIRef(f"https://www.worldcat.org/oclc/{oclc_number}")


# Object
for obj_element in tree.findall(".//tei:event[@type='event'] | .//tei:object[@type='infrastructure'] | .//tei:category[@type='concept']", ns):
    xml_id = obj_element.get("{http://www.w3.org/XML/1998/namespace}id")
    wikidata_url = obj_element.find("tei:idno[@type='Wikidata']", ns).text
    id_to_uri[xml_id] = URIRef(wikidata_url)



for relation in tree.findall(".//tei:relation", ns):
    rel_name = relation.get("name")
    active = relation.get("active").lstrip("#")  
    passive = relation.get("passive").lstrip("#")
    # 「.lstrip("#")」は、「文字列の左端(先頭)から、指定した文字を取り除く」というPythonの文字列操作
    # 「lstrip」は "left strip"(左側を剥がす)の略

    subject = id_to_uri[active]
    predicate = EX[rel_name]
    # EX[rel_name] は http://example.org/relation/ というURLの後ろに、rel_name(="worked_in")をくっつけたURIを作る」という意味
    obj = id_to_uri[passive]

    g.add((subject, predicate, obj))



#  Turtle形式でファイルに書き出す
g.serialize(destination="output.ttl", format="turtle")
# 「serialize」は、「メモリの中にある複雑なデータを、ファイルに保存できる文字列の形に変換する」という意味
print("Transformation is successfully finished! Check output.ttl ")