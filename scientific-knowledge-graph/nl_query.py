from rdflib import Graph, Namespace

BIOKG = Namespace("http://example.org/biokg/")
SNOMED = Namespace("http://snomed.info/id/")
OWL = Namespace("http://www.w3.org/2002/07/owl#")

def run_diabetes_query(rdf_file):
    g = Graph()
    g.parse(rdf_file, format="turtle")

    query = """
    PREFIX : <http://example.org/biokg/>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX snomed: <http://snomed.info/id/>

    SELECT DISTINCT ?patient WHERE {
      ?patient a :Patient ;
               :hasPhenotype ?p .
      ?p :indicatesDisease ?d .
      ?d owl:sameAs snomed:44054006 .
    }
    """

    return [str(row.patient) for row in g.query(query)]



# def handle_user_query(question):
#     plan = plan_query(question)

#     if not validate_plan(plan):
#         raise ValueError("Invalid query plan")

#     if plan["intent"] == "cohort_query":
#         return run_diabetes_query("output/biokg.ttl")

#     if plan["intent"] == "explanation_query":
#         pid = plan["patient_id"]
#         return explain_patient(pid)

if __name__ == "__main__":
    results = run_diabetes_query("output/biokg.ttl")
    print("Patients with diabetes evidence:")
    for r in results:
        print(r)
