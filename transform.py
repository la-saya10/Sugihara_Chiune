from lxml import etree

#  Load the XSLT file
xslt_doc = etree.parse("tei_to_html.xsl")
transform = etree.XSLT(xslt_doc)

# Load the XML file to be transformed
xml_doc = etree.parse("chiune_sugihara.xml")

# Perform the transformation
result = transform(xml_doc)

# Save the result as an HTML file
with open("encoding.html", "w", encoding="utf-8") as f:
    f.write(str(result))

print("Transformation is successfully finished! Check encoding.html")