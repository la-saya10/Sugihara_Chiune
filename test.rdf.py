from lxml import etree
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL, FOAF, XSD, SKOS
from rdflib.namespace import DCTERMS as DCT

# ─────────────────────────────────────────
# 名前空間の定義
# ─────────────────────────────────────────
CRM      = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
SCHEMA   = Namespace("https://schema.org/")
WD       = Namespace("http://www.wikidata.org/entity/")
SUGIHARA = Namespace("http://example.org/sugihara/")

ns = {"tei": "http://www.tei-c.org/ns/1.0"}

# ─────────────────────────────────────────
# TEIファイルを読み込む
# ─────────────────────────────────────────
tree = etree.parse("chiune_sugihara.xml")

# ─────────────────────────────────────────
# RDFグラフの初期化・名前空間のバインド
# ─────────────────────────────────────────
g = Graph()
g.bind("foaf",     FOAF)
g.bind("schema",   SCHEMA)
g.bind("crm",      CRM)
g.bind("skos",     SKOS)
g.bind("dcterms",  DCT)
g.bind("owl",      OWL)
g.bind("wd",       WD)
g.bind("sugihara", SUGIHARA)

# ─────────────────────────────────────────
# ヘルパー関数
# ─────────────────────────────────────────
def get_wikidata_qid(element):
    """idno[@type='Wikidata']からQIDを取得しWD URIRefを返す"""
    idno = element.find("tei:idno[@type='Wikidata']", ns)
    if idno is not None and idno.text:
        url = idno.text.strip()
        qid = url.rstrip("/").split("/")[-1]
        return URIRef(WD[qid])
    return None

def get_text(element, tag):
    """指定タグのテキストを取得"""
    el = element.find(f"tei:{tag}", ns)
    return el.text.strip() if el is not None and el.text else None

# ─────────────────────────────────────────
# xml:id → SUGIHARA URIRef の辞書を作る
# ─────────────────────────────────────────
# 問題③の修正：WikidataのURIではなくSUGIHARA名前空間のURIを主語に使う
id_to_uri = {}

for person in tree.findall(".//tei:person", ns):
    xml_id = person.get("{http://www.w3.org/XML/1998/namespace}id")
    if xml_id:
        id_to_uri[xml_id] = SUGIHARA[xml_id]

for place in tree.findall(".//tei:place", ns):
    xml_id = place.get("{http://www.w3.org/XML/1998/namespace}id")
    if xml_id:
        id_to_uri[xml_id] = SUGIHARA[xml_id]

for org in tree.findall(".//tei:org", ns):
    xml_id = org.get("{http://www.w3.org/XML/1998/namespace}id")
    if xml_id:
        id_to_uri[xml_id] = SUGIHARA[xml_id]

for bibl in tree.findall(".//tei:listBibl/tei:bibl", ns):
    xml_id = bibl.get("{http://www.w3.org/XML/1998/namespace}id")
    if xml_id:
        id_to_uri[xml_id] = SUGIHARA[xml_id]

for el in (tree.findall(".//tei:event", ns) +
           tree.findall(".//tei:category", ns) +
           tree.findall(".//tei:object", ns)):
    xml_id = el.get("{http://www.w3.org/XML/1998/namespace}id")
    if xml_id:
        id_to_uri[xml_id] = SUGIHARA[xml_id]

# ─────────────────────────────────────────
# エンティティ → RDFクラス＋プロパティ
# ─────────────────────────────────────────

# ── listPerson ──
for person in tree.findall(".//tei:person", ns):
    xml_id = person.get("{http://www.w3.org/XML/1998/namespace}id")
    if not xml_id:
        continue
    uri = SUGIHARA[xml_id]

    g.add((uri, RDF.type, FOAF.Person))

    for pn in person.findall("tei:persName", ns):
        lang = pn.get("{http://www.w3.org/XML/1998/namespace}lang")
        if pn.text:
            lit = Literal(pn.text.strip(), lang=lang) if lang else Literal(pn.text.strip())
            g.add((uri, FOAF.name, lit))

    birth = person.find("tei:birth", ns)
    if birth is not None and birth.get("when"):
        g.add((uri, SCHEMA.birthDate, Literal(birth.get("when"), datatype=XSD.date)))

    death = person.find("tei:death", ns)
    if death is not None and death.get("when"):
        g.add((uri, SCHEMA.deathDate, Literal(death.get("when"), datatype=XSD.date)))

    occ = person.find("tei:occupation", ns)
    if occ is not None and occ.text:
        g.add((uri, SCHEMA.jobTitle, Literal(occ.text.strip())))

    wd = get_wikidata_qid(person)
    if wd:
        g.add((uri, OWL.sameAs, wd))

    for idno in person.findall("tei:idno", ns):
        if idno.get("type", "").upper() == "VIAF" and idno.text:
            g.add((uri, OWL.sameAs, URIRef(idno.text.strip())))

# ── listPlace ──
for place in tree.findall(".//tei:place", ns):
    xml_id = place.get("{http://www.w3.org/XML/1998/namespace}id")
    if not xml_id:
        continue
    uri = SUGIHARA[xml_id]

    ptype = place.get("type", "")
    cls = SCHEMA.Museum if ptype == "museum" else SCHEMA.City if ptype == "city" else SCHEMA.Place
    g.add((uri, RDF.type, cls))

    pn = place.find(".//tei:placeName", ns)
    if pn is not None and pn.text:
        g.add((uri, SCHEMA.name, Literal(pn.text.strip())))

    geo = place.find(".//tei:geo", ns)
    if geo is not None and geo.text:
        parts = geo.text.strip().replace(",", "").split()
        if len(parts) == 2:
            g.add((uri, SCHEMA.latitude,  Literal(parts[0], datatype=XSD.decimal)))
            g.add((uri, SCHEMA.longitude, Literal(parts[1], datatype=XSD.decimal)))

    country = place.find(".//tei:country", ns)
    if country is not None and country.text:
        g.add((uri, SCHEMA.addressCountry, Literal(country.text.strip())))

    note = place.find("tei:note", ns)
    if note is not None and note.text:
        g.add((uri, SCHEMA.description, Literal(note.text.strip())))

    wd = get_wikidata_qid(place)
    if wd:
        g.add((uri, OWL.sameAs, wd))

# ── listOrg ──
for org in tree.findall(".//tei:org", ns):
    xml_id = org.get("{http://www.w3.org/XML/1998/namespace}id")
    if not xml_id:
        continue
    uri = SUGIHARA[xml_id]

    g.add((uri, RDF.type, FOAF.Organization))

    for on in org.findall("tei:orgName", ns):
        if on.text:
            g.add((uri, FOAF.name, Literal(on.text.strip())))

    desc = org.find("tei:desc", ns)
    if desc is not None and desc.text:
        g.add((uri, SCHEMA.description, Literal(desc.text.strip())))

    country = org.find(".//tei:country", ns)
    if country is not None and country.text:
        g.add((uri, SCHEMA.addressCountry, Literal(country.text.strip())))

    wd = get_wikidata_qid(org)
    if wd:
        g.add((uri, OWL.sameAs, wd))

# ── listBibl ──
BIBL_CLASS = {"documentary": SCHEMA.Movie, "book": SCHEMA.Book}

for bibl in tree.findall(".//tei:listBibl/tei:bibl", ns):
    xml_id = bibl.get("{http://www.w3.org/XML/1998/namespace}id")
    if not xml_id:
        continue
    uri = SUGIHARA[xml_id]

    btype = bibl.get("type", "book")
    g.add((uri, RDF.type, BIBL_CLASS.get(btype, SCHEMA.Book)))

    title = bibl.find("tei:title", ns)
    if title is not None and title.text:
        g.add((uri, SCHEMA.name, Literal(title.text.strip())))

    author = bibl.find("tei:author", ns)
    if author is not None and author.text:
        g.add((uri, SCHEMA.author, Literal(author.text.strip())))

    for resp in bibl.findall("tei:respStmt", ns):
        role = get_text(resp, "resp")
        name_el = resp.find("tei:name", ns)
        if role and name_el is not None and name_el.text:
            if role.lower() == "director":
                g.add((uri, SCHEMA.director, Literal(name_el.text.strip())))

    pub = bibl.find("tei:publisher", ns)
    if pub is not None and pub.text:
        g.add((uri, SCHEMA.publisher, Literal(pub.text.strip())))

    date = bibl.find("tei:date", ns)
    if date is not None and date.get("when"):
        g.add((uri, SCHEMA.datePublished, Literal(date.get("when"))))

    wd = get_wikidata_qid(bibl)
    if wd:
        g.add((uri, OWL.sameAs, wd))

    for idno in bibl.findall("tei:idno", ns):
        if idno.get("type", "").upper() == "OCLC" and idno.text:
            g.add((uri, SCHEMA.identifier, Literal(f"OCLC:{idno.text.strip()}")))

# ── listEvent ──
for event in tree.findall(".//tei:event", ns):
    xml_id = event.get("{http://www.w3.org/XML/1998/namespace}id")
    if not xml_id:
        continue
    uri = SUGIHARA[xml_id]

    g.add((uri, RDF.type, CRM.E5_Event))

    head = event.find("tei:head", ns)
    if head is not None and head.text:
        g.add((uri, RDFS.label, Literal(head.text.strip(), lang="en")))

    desc_p = event.find(".//tei:p", ns)
    if desc_p is not None and desc_p.text:
        g.add((uri, SCHEMA.description, Literal(desc_p.text.strip())))

    date = event.find("tei:date", ns)
    if date is not None and date.get("when"):
        g.add((uri, SCHEMA.startDate,
               Literal(date.get("when"), datatype=XSD.gYear)))

    wd = get_wikidata_qid(event)
    if wd:
        g.add((uri, OWL.sameAs, wd))

# ── listObject ──
for obj in tree.findall(".//tei:object", ns):
    xml_id = obj.get("{http://www.w3.org/XML/1998/namespace}id")
    if not xml_id:
        continue
    uri = SUGIHARA[xml_id]

    g.add((uri, RDF.type, CRM.E25_Human_Made_Feature))

    name = obj.find(".//tei:objectName", ns)
    if name is not None and name.text:
        g.add((uri, SCHEMA.name, Literal(name.text.strip())))

    note = obj.find("tei:note", ns)
    if note is not None and note.text:
        g.add((uri, SCHEMA.description, Literal(note.text.strip())))

    wd = get_wikidata_qid(obj)
    if wd:
        g.add((uri, OWL.sameAs, wd))

# ── classDecl/category（concept） ──
for cat in tree.findall(".//tei:category", ns):
    xml_id = cat.get("{http://www.w3.org/XML/1998/namespace}id")
    if not xml_id:
        continue
    uri = SUGIHARA[xml_id]

    g.add((uri, RDF.type, SKOS.Concept))

    catdesc = cat.find("tei:catDesc", ns)
    if catdesc is not None and catdesc.text:
        g.add((uri, SKOS.prefLabel, Literal(catdesc.text.strip(), lang="en")))

    note = cat.find("tei:note", ns)
    if note is not None and note.text:
        g.add((uri, SKOS.definition, Literal(note.text.strip(), lang="en")))

    wd = get_wikidata_qid(cat)
    if wd:
        g.add((uri, OWL.sameAs, wd))

# ─────────────────────────────────────────
# listRelation → 既存ボキャブラリーのプロパティ
# ─────────────────────────────────────────
# 問題①の修正：EX:（独自）→ 既存ボキャブラリーのプロパティに置き換え
RELATION_MAP = {
    "servedIn":         SCHEMA.workLocation,
    "affectedBy":       CRM.P15_was_influenced_by,
    "enabledEscapeVia": CRM.P16_used_specific_object,
    "collaboratedWith": SCHEMA.colleague,
    "awardedTitle":     SCHEMA.award,
    "honoredBy":        SCHEMA.memberOf,
    "worksFor":         SCHEMA.worksFor,
    # 逆向き（passive→active）
    "commemoratedAt":   SCHEMA.about,
    "isSubjectOf":      SCHEMA.about,
}

REVERSE_RELATIONS = {"commemoratedAt", "isSubjectOf"}

for relation in tree.findall(".//tei:relation", ns):
    rel_name = relation.get("name")
    active   = relation.get("active", "").lstrip("#")
    passive  = relation.get("passive", "").lstrip("#")

    if not (rel_name and active and passive):
        continue
    if active not in id_to_uri or passive not in id_to_uri:
        continue

    prop = RELATION_MAP.get(rel_name)
    if prop is None:
        continue

    active_uri  = id_to_uri[active]
    passive_uri = id_to_uri[passive]

    if rel_name in REVERSE_RELATIONS:
        g.add((passive_uri, prop, active_uri))
    else:
        g.add((active_uri, prop, passive_uri))

# ─────────────────────────────────────────
# 追加トリプル（conceptual modelで決めた関係）
# ─────────────────────────────────────────




# Soviet occupation → took place at → Kaunas
if "soviet-occupation" in id_to_uri and "kaunas" in id_to_uri:
    g.add((id_to_uri["soviet-occupation"],
           CRM.P7_took_place_at,
           id_to_uri["kaunas"]))

# Transit Visa -> skos:broader 
if "transit-visa" in id_to_uri:
    g.add((id_to_uri["transit-visa"],
           SKOS.broader,
           URIRef(WD["Q170404"])))

# Righteous Among the Nations → inScheme → Yad Vashem
if "righteous-among-nations" in id_to_uri and "yad-vashem" in id_to_uri:
    g.add((id_to_uri["righteous-among-nations"],
           SKOS.inScheme,
           id_to_uri["yad-vashem"]))

# Jan Zwartendijk → workLocation → Kaunas
if "jan-zwartendijk" in id_to_uri and "kaunas" in id_to_uri:
    g.add((id_to_uri["jan-zwartendijk"],
           SCHEMA.workLocation,
           id_to_uri["kaunas"]))

# ─────────────────────────────────────────
# Turtle形式で出力
# ─────────────────────────────────────────
g.serialize(destination="output_test.ttl", format="turtle")
print(f"完了: output.ttl を生成しました（{len(g)} トリプル）")