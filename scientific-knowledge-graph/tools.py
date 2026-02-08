def phenotype_cohort_tool(hpo_id):
    return f"""
    PREFIX : <http://example.org/biokg/>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX hpo: <http://purl.obolibrary.org/obo/HP_>

    SELECT DISTINCT ?patient WHERE {{
      ?patient a :Patient ;
               :hasPhenotype ?p .
      ?p owl:sameAs hpo:{hpo_id} .
    }}
    """

def explanation_tool(patient_id):
    return f"""
    PREFIX : <http://example.org/biokg/>

    SELECT ?lab ?value WHERE {{
      :Patient_{patient_id} :hasLabMeasurement ?lab .
      ?lab :hasValue ?value .
    }}
    """

def disease_cohort_tool(concept_id):
    return f"""
    PREFIX : <http://example.org/biokg/>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX snomed: <http://snomed.info/id/>

    SELECT DISTINCT ?patient WHERE {{
      ?patient a :Patient ;
               :hasPhenotype ?p .
      ?p :indicatesDisease ?d .
      ?d owl:sameAs snomed:{concept_id} .
    }}
    """

def variant_carrier_tool(gene_symbol):
    return f"""
    PREFIX : <http://example.org/biokg/>

    SELECT DISTINCT ?patient WHERE {{
      ?patient :hasVariant ?v .
      ?v :affectsGene :{gene_symbol} ;
         :hasClinicalSignificance "pathogenic" .
    }}
    """

def gene_expression_tool(gene_symbol):
    return f"""
    PREFIX : <http://example.org/biokg/>

    SELECT DISTINCT ?patient WHERE {{
      ?patient :hasGeneExpression ?e .
      ?e :affectsGene :{gene_symbol} ;
         :log2FoldChange ?fc .
      FILTER (?fc < -1.0)
    }}
    """

def protein_abundance_tool(protein_symbol):
    return f"""
    PREFIX : <http://example.org/biokg/>

    SELECT DISTINCT ?patient WHERE {{
      ?patient :hasProteinAbundance ?p .
      ?p :affectsProtein :{protein_symbol} ;
         :abundance ?a .
      FILTER (?a > 2.0)
    }}
    """
