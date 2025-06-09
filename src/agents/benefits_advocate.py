"""
The Benefits Advocate Agent.

This agent is a specialist in Medicare and insurance benefits. Its goals are:
1. To understand the user's questions about benefits, plans, and costs.
2. To use the `find_plans_with_benefits` tool to query a real-time Databricks database for Medicare Advantage plans.
3. To present the findings to the user in a clear and helpful manner.
"""

import ast
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_experimental.tools import tool
from langchain_openai import ChatOpenAI

@tool
def find_plans_with_benefits(required_benefits: list[str]) -> str:
    """
    Finds Medicare Advantage plans that include all of the specified supplemental benefits.
    The input should be a list of strings, where each string is a benefit to search for.
    Example: ['dental', 'vision', 'transportation']
    """
    # Build a WHERE clause from the list of required benefits
    # Assumes benefit names in the database are like 'has_dental', 'has_vision', etc.
    where_conditions = [f"has_{benefit.strip().lower()} = true" for benefit in required_benefits]
    where_clause = " AND ".join(where_conditions)

    query = f"""
        SELECT pbp_a_hnumber, pbp_a_plan_identifier, all_benefits
        FROM databricksday.default.medicare_benefits_analysis
        WHERE {where_clause}
        LIMIT 5
    """
    print(f"Executing query: {query}")
    try:
        # Import spark here to avoid issues when not in a Databricks environment
        from pyspark.sql import SparkSession
        spark = SparkSession.getActiveSession()
        if spark is None:
            return "Error: Could not connect to the Databricks database."
        
        df = spark.sql(query).toPandas()
        if df.empty:
            return "No plans found that match all of your required benefits."
        # Return the results as a JSON string
        return df.to_json(orient='records', indent=2)
    except Exception as e:
        # In a real app, you'd want more robust error logging
        print(f"Error querying data: {e}")
        return f"An error occurred while querying the benefits database."

# System prompt for the agent
SYSTEM_PROMPT = """You are the "Benefits Advocate," an AI assistant specializing in Medicare.
Your role is to help users find Medicare Advantage plans that fit their needs.
You have access to a tool called `find_plans_with_benefits` that connects to a real-time Databricks database of Medicare plans.

- When the user asks for plans with specific benefits (e.g., "dental," "vision," "transportation"), you MUST use the `find_plans_with_benefits` tool.
- The tool expects a list of benefit names. You must extract the required benefits from the user's query and pass them to the tool.
- Once you get the results from the tool, present them to the user in a clear, easy-to-understand format.
- If no plans are found, inform the user gracefully.
- Do not make up information. Only provide information returned from the tool.
"""

def get_benefits_advocate_agent():
    """Builds and returns the Benefits Advocate Agent."""
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    tools = [find_plans_with_benefits]
    agent = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}")
    ]) | llm.bind_tools(tools)
    
    return agent, tools
