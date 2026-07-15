from rdflib import Graph

g = Graph()
g.parse("output_v3.ttl", format="turtle")      # rdf from xml
g.parse("output_from_csv.ttl", format="turtle")   # rdf from csv

g.serialize(destination="output_combined.ttl", format="turtle")
print(f"Merge completed: {len(g)} triples saved to output_combined.ttl.")