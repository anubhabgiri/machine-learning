import random
import numpy as np
import json

random.seed(42)
np.random.seed(42)

GENES = ["BRCA1", "TP53", "EGFR", "INS", "APOE"]
METABOLITES = ["Glucose", "Lactate"]
LABS = ["HbA1c", "Fasting Glucose"]

def generate_variant(gene):
    if random.random() < 0.15:  # 15% chance
        return {
            "gene": gene,
            "variant": f"{gene}_var1",
            "type": random.choice(["SNV", "indel"]),
            "zygosity": random.choice(["heterozygous", "homozygous"]),
            "significance": random.choice(["pathogenic", "VUS"])
        }
    return None

def generate_patient(pid):
    genomics = list(filter(None, [generate_variant(g) for g in GENES]))

    transcriptomics = [
        {"gene": g, "log2fc": round(np.random.normal(0, 1.2), 2)}
        for g in GENES
    ]

    proteomics = [
        {"protein": g, "abundance": round(np.random.lognormal(0.5, 0.4), 2)}
        for g in GENES
    ]

    glucose = round(np.random.normal(110, 25), 1)
    hba1c = round(np.random.normal(5.6, 1.2), 1)

    metabolomics = [
        {"metabolite": "Glucose", "concentration": glucose},
        {"metabolite": "Lactate", "concentration": round(np.random.normal(1.5, 0.4), 2)}
    ]

    labs = [
        {"test": "HbA1c", "value": hba1c, "unit": "%"},
        {"test": "Fasting Glucose", "value": glucose, "unit": "mg/dL"}
    ]

    return {
        "patient_id": pid,
        "genomics": genomics,
        "transcriptomics": transcriptomics,
        "proteomics": proteomics,
        "metabolomics": metabolomics,
        "labs": labs
    }

patients = [generate_patient(f"P{str(i).zfill(3)}") for i in range(1, 16)]

with open("synthetic_multiomics.json", "w") as f:
    json.dump(patients, f, indent=2)

print("Generated", len(patients), "patients")
