from lxml import etree

# XSLTファイルを読み込む
xslt_doc = etree.parse("tei_to_html.xsl")
transform = etree.XSLT(xslt_doc)

# 変換対象のXMLファイルを読み込む
xml_doc = etree.parse("chiune_sugihara.xml")

# 変換を実行
result = transform(xml_doc)

# 結果をHTMLファイルとして保存
with open("encoding.html", "w", encoding="utf-8") as f:
    f.write(str(result))

print("Transformation is successfully finished! Check encoding.html")