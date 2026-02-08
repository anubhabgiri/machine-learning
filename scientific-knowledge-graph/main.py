import json
import logging
from google import genai
import os
from rdflib import Graph

from dotenv import load_dotenv
from tools import (
    phenotype_cohort_tool, 
    explanation_tool, 
    disease_cohort_tool, 
    variant_carrier_tool,
    gene_expression_tool,
    protein_abundance_tool
)
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("biokg-agent")

# The client gets the API key from the environment variable GEMINI_API_KEY
client = genai.Client()
QUERY_TOOLS = {}

def plan_query(user_question):
    prompt = """
    You are an ontology-aware biomedical query planner.

    You MUST output a JSON object that EXACTLY matches this schema:

    {{
    "intent": "cohort_query | explanation_query | genomics_query | transcriptomics_query | proteomics_query",
    "patient_id": "optional string (required only for explanation_query)",
    "ontology_target": {{
        "label": "string",
        "ontology": "SNOMED | HPO | LOINC | HGNC | GO",
        "id": "string",
        "cui": "optional string",
        "role": "target | constraint"
    }}
    }}

    Rules:
    - Output JSON ONLY
    - No explanation
    - No extra keys
    - No comments
    - No trailing text
    - Do NOT answer the question
    - Use only SNOMED, HPO, HGNC or LOINC identifiers
    - If you cannot comply, output: {{"intent": "unknown"}}

    User question:
    "{question}"
    """.format(question=user_question)

    logger.debug("Sending planning prompt to LLM. Prompt length=%d", len(prompt))
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt
    )
    logger.debug("Received planner response (raw): %s", getattr(response, "text", str(response)))
    try:
        plan = json.loads(response.text)
        logger.debug("Parsed plan JSON: %s", plan)
    except Exception as e:
        logger.exception("Failed to parse planner response as JSON")
        raise

    return plan

def validate_schema(obj):
    logger.debug("Validating plan schema: %s", obj)
    if not isinstance(obj, dict):
        logger.error("Plan is not a dict")
        return False

    if "intent" not in obj:
        logger.error("Plan missing 'intent'")
        return False

    valid_intents = ["cohort_query", "explanation_query", "genomics_query", "transcriptomics_query", "proteomics_query"]
    if obj["intent"] not in valid_intents:
        logger.error("Invalid intent: %s", obj.get("intent"))
        return False

    if "ontology_target" not in obj:
        logger.error("Plan missing 'ontology_target'")
        return False

    ot = obj["ontology_target"]

    for key in ["label", "ontology", "id"]:
        if key not in ot:
            logger.error("ontology_target missing key: %s", key)
            return False

    if ot["ontology"] not in ["SNOMED", "HPO", "LOINC", "HGNC", "GO"]:
        logger.error("Unsupported ontology: %s", ot.get("ontology"))
        return False

    if obj["intent"] == "explanation_query" and "patient_id" not in obj:
        logger.error("explanation_query missing 'patient_id'")
        return False

    logger.debug("Plan schema validated successfully")
    return True

# Map the planner's "cohort_query" intent for both SNOMED and HPO to their tools
QUERY_TOOLS[("cohort_query", "SNOMED")] = disease_cohort_tool
QUERY_TOOLS[("cohort_query", "HPO")] = phenotype_cohort_tool
QUERY_TOOLS[("explanation_query", "SNOMED")] = explanation_tool
QUERY_TOOLS[("genomics_query", "HGNC")] = variant_carrier_tool
QUERY_TOOLS[("transcriptomics_query", "HGNC")] = gene_expression_tool
QUERY_TOOLS[("proteomics_query", "HGNC")] = protein_abundance_tool


def select_tool(plan):
    logger.debug("Selecting tool for plan: %s", plan)
    intent = plan["intent"]

    # The planner schema uses "ontology_target"
    ot = plan.get("ontology_target")
    if not ot:
        logger.error("Plan missing 'ontology_target'")
        raise ValueError("Plan missing 'ontology_target'")

    ontology = ot.get("ontology")
    if not ontology:
        logger.error("ontology_target missing 'ontology'")
        raise ValueError("ontology_target missing 'ontology'")
    
    # cohort query, SNOMED
    key = (intent, ontology)
    logger.debug("Tool lookup key: %s", key)

    if key not in QUERY_TOOLS:
        logger.error("No tool registered for key: %s", key)
        raise ValueError(f"No tool for {key}")

    tool_fn = QUERY_TOOLS[key]
    if intent == "explanation_query":
        patient_id = plan.get("patient_id")
        logger.debug("Using explanation tool for patient_id=%s", patient_id)
        sparql = tool_fn(patient_id)
    else:
        logger.debug("Using other tool for ontology id=%s", ot.get("id"))
        sparql = tool_fn(ot["id"])

    # Log a short preview of the generated SPARQL
    preview = "\n".join(line for line in sparql.splitlines() if line.strip())[:800]
    logger.debug("Generated SPARQL preview:\n%s", preview)
    return sparql


def execute_agent_query(plan, rdf_path="output/biokg.ttl"):
    logger.info("Executing agent query for plan with RDF path: %s", rdf_path)
    sparql = select_tool(plan)

    g = Graph()
    try:
        logger.debug("Parsing RDF file: %s", rdf_path)
        g.parse(rdf_path, format="turtle")
        logger.debug("RDF parsed successfully. Graph has %d triples", len(g))
    except Exception as e:
        logger.exception("Failed to parse RDF file")
        raise

    try:
        logger.debug("Running SPARQL query...")
        qres = g.query(sparql)
        # Materialize results to list for logging
        results_list = list(qres)
        logger.info("SPARQL query returned %d rows", len(results_list))
        # Optionally log first few rows
        for i, row in enumerate(results_list[:5]):
            logger.debug("Row %d: %s", i, tuple(row))
        return results_list
    except Exception:
        logger.exception("SPARQL query failed")
        raise

def answer_question(user_question):
    logger.info("Answering question: %s", user_question)
    # plan = plan_query(user_question)      # LLM planner
    plan = {
        "intent": "genomics_query",
        "ontology_target": {
            "label": "BRCA1",
            "ontology": "HGNC",
            "id": "HGNC:1100",
            "cui": "C0079038",
            "role": "target"
        }
        }
    if not validate_schema(plan):
        logger.error("Plan failed validation: %s", plan)
        raise ValueError("Invalid plan")

    results = execute_agent_query(plan)   # auto tool selection
    logger.info("Answering finished. %d results obtained", len(results) if isinstance(results, list) else 0)

    return results

if __name__ == "__main__":
    """
    SAMPLE QUESTIONS:
    ----------- Phenotypes --------------
    1. 'Which patients show evidence of diabetes?' - metalobomics cohort query (SNOMED)
    ----------- Genomics ----------------

    “Which patients carry pathogenic BRCA1 variants?”

    “Find patients with APOE risk variants”

    ----------- Transcriptomics ------------

    “Which patients show TP53 downregulation?”

    “Patients with INS overexpression”

    ----------- Proteomics ------------

    “Which patients show EGFR overexpression?”

    “Protein abundance changes in APOE”

    ----------- Multi-omics ---------------

    “Patients with BRCA1 mutation AND TP53 downregulation”
    """
    try:
        user_question = input("User question: ")
        results = answer_question(user_question)
        # Print human-readable output for the CLI run
        print("\nQuery results:")
        if not results:
            print("No results.")
        else:
            for row in results:
                # rows may be RDFlib Row objects or tuples
                print(tuple(row))
    except Exception as e:
        logger.exception("Unhandled exception during main execution")
        raise
