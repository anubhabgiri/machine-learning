import json
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, OWL, XSD

# ----------------------------
# Namespaces
# ----------------------------
BIOKG = Namespace("http://example.org/biokg/")
LOINC = Namespace("http://loinc.org/rdf/")
HPO = Namespace("http://purl.obolibrary.org/obo/HP_")
UMLS = Namespace("http://linkedlifedata.com/resource/umls/id/")

# ----------------------------
# Load Graph + TBox
# ----------------------------
g = Graph()
g.parse("namespaces.ttl", format="turtle")
g.parse("biokg.owl", format="turtle")

# ----------------------------
# Load synthetic data
# ----------------------------
with open("synthetic_multiomics.json") as f:
    patients = json.load(f)

# ----------------------------
# Constants (data-level only)
# ----------------------------
HBA1C_LOINC = LOINC["4548-4"]
FASTING_GLUCOSE_LOINC = LOINC["1558-6"]

HYPERGLYCEMIA_HPO = HPO["0003074"]
HYPERGLYCEMIA_CUI = "C0020456"

# ----------------------------
# Helper: emit hyperglycemia phenotype
# ----------------------------
def add_hyperglycemia(patient_uri, pid):
    phenotype_uri = BIOKG[f"Hyperglycemia_{pid}"]

    g.add((phenotype_uri, RDF.type, BIOKG.Phenotype))
    g.add((phenotype_uri, OWL.sameAs, HYPERGLYCEMIA_HPO))
    g.add((phenotype_uri, UMLS.cui, Literal(HYPERGLYCEMIA_CUI)))

    # Attach to patient
    g.add((patient_uri, BIOKG.hasPhenotype, phenotype_uri))

    # IMPORTANT: attach to specific disease (Type 2)
    g.add((phenotype_uri, BIOKG.indicatesDisease, BIOKG.Type2DiabetesMellitus))


# ----------------------------
# JSON → RDF (ABox only)
# ----------------------------
for patient in patients:
    pid = patient["patient_id"]
    patient_uri = BIOKG[f"Patient_{pid}"]

    g.add((patient_uri, RDF.type, BIOKG.Patient))

    for lab in patient.get("labs", []):
        test = lab["test"]
        value = lab["value"]

        lab_uri = BIOKG[f"{test.replace(' ', '')}_{pid}"]

        g.add((lab_uri, RDF.type, BIOKG.LabMeasurement))
        g.add((lab_uri, BIOKG.hasValue, Literal(value, datatype=XSD.decimal)))
        g.add((patient_uri, BIOKG.hasLabMeasurement, lab_uri))

        # HbA1c rule
        if test == "HbA1c":
            g.add((lab_uri, BIOKG.usesTest, HBA1C_LOINC))
            if value >= 6.5:
                add_hyperglycemia(patient_uri, pid)

        # Fasting glucose rule
        if test == "Fasting Glucose":
            g.add((lab_uri, BIOKG.usesTest, FASTING_GLUCOSE_LOINC))
            if value >= 126:
                add_hyperglycemia(patient_uri, pid)

# ----------------------------
# Serialize
# ----------------------------
g.serialize("output/biokg.ttl", format="turtle")
print("RDF graph generated: output/biokg.ttl")
