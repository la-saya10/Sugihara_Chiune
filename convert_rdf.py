from lxml import etree
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, FOAF, RDFS, OWL, DCTERMS

# 1. XML（TEI）ファイルの読み込み
tree = etree.parse('hokusai_tei.xml')
root = tree.getroot()
ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

# 2. 空のRDFグラフを作る
g = Graph()

# 名前空間（ボキャブラリ）の設定
EX = Namespace("http://example.org/hokusai/")
SCHEMA = Namespace("https://schema.org/")
REL = Namespace("http://purl.org/vocab/relationship/") # 関係性表現用の任意語彙

g.bind("ex", EX)
g.bind("foaf", FOAF)
g.bind("owl", OWL)
g.bind("rdfs", RDFS)
g.bind("dcterms", DCTERMS)
g.bind("schema", SCHEMA)

# ==========================================
# 💾 Step 1: person の処理（改善版）
# ==========================================
for person in root.findall('.//tei:listPerson/tei:person', ns):
    person_id = person.get('{http://www.w3.org/XML/1998/namespace}id')
    if not person_id:
        continue
    
    subject_uri = EX[person_id]
    g.add((subject_uri, RDF.type, FOAF.Person))
    
    # 全件名前ループ（xml:lang対応）
    for pname in person.findall('tei:persName', ns):
        lang = pname.get('{http://www.w3.org/XML/1998/namespace}lang', '')
        if pname.text:
            g.add((subject_uri, FOAF.name, Literal(pname.text.strip(), lang=lang)))
            
    # 全件外部IDループ（owl:sameAs）
    for idno in person.findall('tei:idno', ns):
        if idno.text:
            g.add((subject_uri, OWL.sameAs, URIRef(idno.text.strip())))

# ==========================================
# 💾 Step 2: place の処理 (listPlace)
# ==========================================
for place in root.findall('.//tei:listPlace/tei:place', ns):
    place_id = place.get('{http://www.w3.org/XML/1998/namespace}id')
    if not place_id:
        continue
        
    place_uri = EX[place_id]
    g.add((place_uri, RDF.type, SCHEMA.Place)) # schema:Place を適用
    
    # 場所名の全件処理
    for pname in place.findall('tei:placeName', ns):
        lang = pname.get('{http://www.w3.org/XML/1998/namespace}lang', '')
        if pname.text:
            g.add((place_uri, RDFS.label, Literal(pname.text.strip(), lang=lang)))
            
    # 外部ID（WikidataやGeoNamesなど）へのリンク
    for idno in place.findall('tei:idno', ns):
        if idno.text:
            g.add((place_uri, OWL.sameAs, URIRef(idno.text.strip())))
            
    # 緯度経度（geoタグ）があれば座標情報として追加
    geo = place.find('tei:location/tei:geo', ns)
    if geo is not None and geo.text:
        g.add((place_uri, SCHEMA.geo, Literal(geo.text.strip())))

# ==========================================
# 💾 Step 3: bibl の処理 (listBibl)
# ==========================================
for bibl in root.findall('.//tei:listBibl/tei:bibl', ns):
    bibl_id = bibl.get('{http://www.w3.org/XML/1998/namespace}id')
    if not bibl_id:
        continue
        
    bibl_uri = EX[bibl_id]
    g.add((bibl_uri, RDF.type, SCHEMA.Book)) # 文献・書籍型
    
    # タイトルの全件処理
    for title in bibl.findall('tei:title', ns):
        lang = title.get('{http://www.w3.org/XML/1998/namespace}lang', '')
        if title.text:
            g.add((bibl_uri, DCTERMS.title, Literal(title.text.strip(), lang=lang)))
            
    # 著者（author）がいればリンク（URIまたは文字列）
    for author in bibl.findall('tei:author', ns):
        author_ref = author.get('ref')
        if author_ref:
            # ref="#Hokusai" のような内部リンクをURIに変換
            author_uri = EX[author_ref.replace('#', '')]
            g.add((bibl_uri, DCTERMS.creator, author_uri))
        elif author.text:
            g.add((bibl_uri, DCTERMS.creator, Literal(author.text.strip())))

# ==========================================
# 💾 Step 4: listRelation の処理
# ==========================================
for relation in root.findall('.//tei:listRelation/tei:relation', ns):
    # active（主語側）と mutual/passive（目的語側）のURIを取得
    active_ref = relation.get('active')
    passive_ref = relation.get('passive') or relation.get('mutual')
    name_attr = relation.get('name') # 関係性の名前（例: studentOf, childOf）
    
    if active_ref and passive_ref and name_attr:
        # `#` を取り除いて独自のベースURIと結合
        sub = EX[active_ref.replace('#', '')]
        obj = EX[passive_ref.replace('#', '')]
        pred = REL[name_attr] # 関係性を表す述語にする
        
        # トリプル追加（例：北斎 ──[studentOf]──> 勝川春章）
        g.add((sub, pred, obj))

# ==========================================
# 💾 Step 5: 書き出して内容確認
# ==========================================
g.serialize(destination='hokusai_complete.ttl', format='turtle', encoding='utf-8')
# 確認用コードを末尾に追加
for s, p, o in g:
    print(s, p, o)