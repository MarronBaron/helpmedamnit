import pandas as pd
import ast

def find_plans_with_benefits(required_benefits: str) -> str:
    """
    Finds Medicare Advantage plans that include all of the specified supplemental benefits.
    """
    try:
        benefits_list = ast.literal_eval(required_benefits)
        if not isinstance(benefits_list, list):
            raise ValueError("Input could not be parsed into a list.")
    except (ValueError, SyntaxError) as e:
        return f"Error: Invalid input format. Expected a string representation of a list. {e}"

    # Build a WHERE clause from the list of required benefits
    where_conditions = [f"has_{benefit.strip()} = true" for benefit in benefits_list]
    where_clause = " AND ".join(where_conditions)

    query = f"""
        SELECT pbp_a_hnumber, pbp_a_plan_identifier, all_benefits
        FROM databricksday.default.medicare_benefits_analysis
        WHERE {where_clause}
        LIMIT 5
    """
    print(f"Executing query: {query}")
    try:
        # Import spark here to avoid issues in local testing
        from pyspark.sql import SparkSession
        spark = SparkSession.getActiveSession()
        if spark is None:
            return "Error: No active Spark session available for data querying."
        
        df = spark.sql(query).toPandas()
        if df.empty:
            return "No plans found with the specified benefits."
        return df.to_json(orient='records', indent=2)
    except Exception as e:
        return f"Error querying data: {e}"

class BenefitsAdvocate:
    def __init__(self, benefits_data: pd.DataFrame):
        """
        Initializes the agent with benefits data.
        
        Args:
            benefits_data (pd.DataFrame): A DataFrame containing benefits/programs info.
        """
        self.benefits_data = benefits_data
        print(f"Benefits Advocate agent initialized with {len(benefits_data)} benefits records.")

    def run(self, query: str) -> str:
        """
        Handles insurance fights by analyzing queries for specific benefits and finding relevant plans.
        """
        print("Benefits Advocate agent activated.")
        
        # Simple benefit extraction logic - in production this would use an LLM
        benefits_mentioned = []
        query_lower = query.lower()
        
        benefit_keywords = {
            'dental': 'dental',
            'fitness': 'fitness', 
            'transportation': 'transportation',
            'acupuncture': 'acupuncture',
            'chiropractic': 'chiropractic',
            'dme': 'dme',
            'home_health': 'home_health',
            'otc_ssbci': 'otc'
        }
        
        for benefit, keyword in benefit_keywords.items():
            if keyword in query_lower:
                benefits_mentioned.append(benefit)
        
        if benefits_mentioned:
            print(f"Found benefits: {benefits_mentioned}")
            benefits_str = str(benefits_mentioned)
            plans_data = find_plans_with_benefits(benefits_str)
            return f"BENEFITS ADVOCATE RESPONSE: I found Medicare plans with {', '.join(benefits_mentioned)} benefits:\n\n{plans_data}"
        else:
            return f"BENEFITS ADVOCATE RESPONSE: I'm analyzing your query '{query}' for Medicare benefits. Could you specify which benefits you're interested in? (dental, fitness, transportation, etc.)"
