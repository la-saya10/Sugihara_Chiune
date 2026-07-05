 levels (Work → Expression → Manifestation → Item) instead of a single node. Finally, every entity is linked to its DBpedia twin with owl:sameAs, so the dataset connects outward to the wider web.

# ============================================================
# CSV -> RDF transformation
#
# This script reads every CSV file in the ../csv folder and turns
# the "subject, predicate, object" rows into RDF triples, using the
# same classes and properties as our conceptual model.
#
# The CSV files hold the EXTRA data (architects, parliament, central
# bank, language, emblem, dates, dimensions...) that is not written
# in the Wikipedia text, so it is not in the TEI file.
#
# Run it from the "Knowledge representation" folder:
#     python3 csv_to_rdf.py
# ============================================================

import os
import csv                                  # built-in library to read CSV
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD, FOAF, OWL   # rdf:type, xsd: datatypes, foaf:, owl:

# ----- 1. Namespaces (same prefixes as the conceptual model) -----
CRM    = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
SCHEMA = Namespace("https://schema.org/")
SKOS   = Namespace("http://www.w3.org/2004/02/skos/core#")
DCT    = Namespace("http://purl.org/dc/terms/")
FRBR   = Namespace("http://purl.org/vocab/frbr/core#")     # FRBR Work/Expression/Manifestation/Item
WDT    = Namespace("http://www.wikidata.org/prop/direct/")
WD     = Namespace("http://www.wikidata.org/entity/")
DBP    = Namespace("http://dbpedia.org/resource/")         # the DBpedia twin of each entity
# Our own namespace, for the FRBR levels of Nutuk that have no Wikidata id.
EX     = Namespace("https://kubrato.github.io/KnowledgeRepresentation-Organization/id/")

# ----- 2. Every entity id used in the CSV files -> its Wikidata URI -----
# The first 11 are the same entities as in the TEI file (so the two RDF
# datasets join on the same URIs). The last 6 are the extra entities.
WIKIDATA = {
    "ataturk": "Q5152",   "turkey": "Q43",        "chp": "Q19079",
    "anitkabir": "Q615404", "tl_banknote": "Q172872", "nutuk": "Q2005693",
    "incredible_turk": "Q31190822", "republic_day": "Q803181",
    "ankara": "Q3640", "kemalism": "Q269443", "law_5816": "Q1519065",
    # extra entities (only in the CSV files)
    "onat": "Q5372464", "arda": "Q6065347", "tbmm": "Q274918",
    "tcmb": "Q580829", "turkish_language": "Q256", "six_arrows": "Q6030041",
}

# ----- 2b. The same entities in DBpedia (for owl:sameAs links) -----
# Each value is the DBpedia article name. "incredible_turk" has no English
# Wikipedia article, so it has no DBpedia twin and is left out on purpose.
DBPEDIA = {
    "ataturk": "Mustafa_Kemal_Atatürk", "turkey": "Turkey",
    "chp": "Republican_People's_Party", "anitkabir": "Anıtkabir",
    "tl_banknote": "Turkish_lira", "nutuk": "Nutuk",
    "republic_day": "Republic_Day_(Turkey)", "ankara": "Ankara",
    "kemalism": "Kemalism",
    "law_5816": "Law_on_crimes_committed_against_Atatürk",
    "onat": "Emin_Halid_Onat", "arda": "Orhan_Arda",
    "tbmm": "Grand_National_Assembly_of_Turkey",
    "tcmb": "Central_Bank_of_the_Republic_of_Turkey",
    "turkish_language": "Turkish_language", "six_arrows": "The_Six_Arrows",
}

# ----- 3. The conceptual model mapping -----
# "has type" value (in the CSV) -> the class of that entity.
TYPE_CLASS = {
    "mausoleum": SCHEMA.Mausoleum, "city": SCHEMA.City,
    "political party": SCHEMA.PoliticalParty, "emblem": CRM.E36_Visual_Item,
    "language": CRM.E56_Language, "person": CRM.E21_Person,
    "assembly": CRM.E74_Group, "organization": CRM.E74_Group,
    "movie": SCHEMA.Movie, "concept": SKOS.Concept,
    "legislation": SCHEMA.Legislation,
    "event": SCHEMA.Event, "object": CRM.E84_Information_Carrier,
    "country": SCHEMA.Country,
    # Nutuk is modelled with the four FRBR levels (Work -> Expression ->
    # Manifestation -> Item) instead of a single schema:Book node.
    "work": FRBR.Work, "expression": FRBR.Expression,
    "manifestation": FRBR.Manifestation, "item": FRBR.Item,
}

# Every CSV predicate -> the property it becomes in RDF.
# We spread the predicates over several vocabularies (schema, crm, dct, foaf,
# skos, frbr, wdt) instead of leaning only on schema: and crm:.
PROP = {
    "has title": SCHEMA.name,
    "has construction date": DCT.created,
    "has foundation date": SCHEMA.foundingDate,
    "has publication date": DCT.issued,
    "has release date": DCT.issued,
    "has date": DCT.date,
    "has area": CRM.P43_has_dimension,
    "has genre": SCHEMA.genre,
    "is dedicated to": CRM.P67_refers_to,
    "is located in": DCT.spatial,
    "has architect": SCHEMA.architect,
    "hosts": CRM.P7i_witnessed,
    "is residence of": CRM.P74i_is_current_or_former_residence_of,
    "is founded by": SCHEMA.founder,
    "is based in": SCHEMA.location,
    "follows": DCT.subject,
    "has flag": CRM.P138i_has_representation,
    "is about": DCT.subject,
    "is enacted by": DCT.creator,
    "protects": SCHEMA.about,
    "has author": FOAF.maker,
    "has language": DCT.language,
    "is published in": SCHEMA.locationCreated,
    "is delivered to": SCHEMA.about,
    "depicts": FOAF.depicts,
    "is issued by": CRM.P108i_was_produced_by,
    "commemorates": DCT.subject,
    "is celebrated in": DCT.spatial,
    "had participant": CRM.P11_had_participant,
    "has capital": WDT.P36,
    "has currency": CRM.P108_has_produced,
    "relates to": DCT.subject,
    "has official language": DCT.language,
    "is agency of": SCHEMA.parentOrganization,
    "is defined by": SKOS.related,
    "is based on": CRM.P67_refers_to,
    # FRBR (WEMI) links used to model Nutuk at four levels.
    "is realised in": FRBR.realization,    # Work       -> Expression
    "is embodied in": FRBR.embodiment,     # Expression -> Manifestation
    "is exemplified by": FRBR.exemplar,    # Manifestation -> Item
}

# Predicates whose object is a literal value (text or number), not an entity.
DATE_PREDS    = {"has construction date", "has foundation date",
                 "has publication date", "has release date", "has date"}
DECIMAL_PREDS = {"has area"}
STRING_PREDS  = {"has title", "has genre"}


# Helper: turn an entity id ("ankara") into its URI. Most entities are
# Wikidata entities; the extra FRBR levels of Nutuk live in our own (EX)
# namespace because they have no Wikidata id.
def uri(entity_id):
    if entity_id in WIKIDATA:
        return URIRef(WD + WIKIDATA[entity_id])
    return URIRef(EX + entity_id)


# ----- 4. Prepare the graph -----
g = Graph()
g.bind("crm", CRM)
g.bind("schema", SCHEMA)
g.bind("skos", SKOS)
g.bind("dct", DCT)
g.bind("foaf", FOAF)
g.bind("frbr", FRBR)
g.bind("owl", OWL)
g.bind("wdt", WDT)
g.bind("wd", WD)
g.bind("dbpedia", DBP)

# ----- 5. Read every CSV file in the ../csv folder -----
HERE = os.path.dirname(os.path.abspath(__file__))   # folder of this script (to_rdf)
BASE = os.path.dirname(HERE)                         # one level up: "Knowledge representation"
csv_dir = os.path.join(BASE, "csv")

for filename in sorted(os.listdir(csv_dir)):
    if not filename.endswith(".csv"):
        continue
    with open(os.path.join(csv_dir, filename), encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)                        # skip the header row
        for row in reader:
            # Skip empty lines and comment lines (they start with "#").
            if not row or row[0].strip().startswith("#"):
                continue
            subject, predicate, obj = (cell.strip() for cell in row)

            # Case A: "has type" -> rdf:type with the class of the entity.
            if predicate == "has type":
                g.add((uri(subject), RDF.type, TYPE_CLASS[obj]))
                # A person is also a foaf:Person (CIDOC-CRM + FOAF together).
                if obj == "person":
                    g.add((uri(subject), RDF.type, FOAF.Person))

            # Case B: the object is a date literal.
            # A full date (YYYY-MM-DD) is xsd:date; a year on its own is xsd:gYear.
            elif predicate in DATE_PREDS:
                date_type = XSD.date if obj.count("-") == 2 else XSD.gYear
                g.add((uri(subject), PROP[predicate], Literal(obj, datatype=date_type)))

            # Case C: the object is a number (we keep only the number, not the unit).
            elif predicate in DECIMAL_PREDS:
                number = obj.split()[0]
                g.add((uri(subject), PROP[predicate], Literal(number, datatype=XSD.decimal)))

            # Case D: the object is a plain text literal.
            elif predicate in STRING_PREDS:
                g.add((uri(subject), PROP[predicate], Literal(obj)))

            # Case E: the object is another entity -> use its URI.
            else:
                g.add((uri(subject), PROP[predicate], uri(obj)))

# ----- 5b. Link every entity to its DBpedia twin with owl:sameAs -----
# This is the Linked Open Data step: it says "this Wikidata entity and that
# DBpedia entity are the same real-world thing", so our data joins the wider web.
for entity_id, dbpedia_title in DBPEDIA.items():
    g.add((uri(entity_id), OWL.sameAs, URIRef(DBP + dbpedia_title)))

# ----- 6. Write the RDF to a Turtle file -----
out_file = os.path.join(BASE, "turtle", "ataturk_csv.ttl")
g.serialize(destination=out_file, format="turtle")
print("Done. Wrote", len(g), "triples to", out_file)