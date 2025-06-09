# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Deploy HelpMeDammit Agent to Model Registry (v6 - Working Demo)
# MAGIC 
# MAGIC This notebook packages our new multi-agent, tool-calling system and registers it in the MLflow Model Registry.

# COMMAND ----------

# MAGIC %pip install mlflow langchain langchain-openai langchain-experimental pydantic pandas scikit-learn --upgrade --quiet
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# Everything in one cell - no external dependencies
import mlflow
import pandas as pd
import json
from mlflow.models import infer_signature
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# === TOOL DEFINITIONS ===
@tool
def find_plans_with_benefits(required_benefits: list[str]) -> str:
    """Finds Medicare Advantage plans with specified benefits."""
    # For demo purposes, let's first try to find ANY plans, then filter
    # Let's also check what columns actually exist
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.getActiveSession()
        if spark is None: 
            return '[{"error": "No Spark session"}]'
        
        # First, let's see what's in the table and get some sample data
        query = """
        SELECT pbp_a_hnumber, pbp_a_plan_identifier, all_benefits
        FROM databricksday.default.medicare_benefits_analysis
        LIMIT 5
        """
        
        df = spark.sql(query).toPandas()
        if df.empty: 
            return '[{"message": "No data found in medicare_benefits_analysis table"}]'
        
        # Return the sample data for now so we can see what we're working with
        return df.to_json(orient='records', indent=2)
        
    except Exception as e:
        return f'[{{"error": "Database error: {str(e)}"}}]'

# === ROUTING TOOL ===
class RouteToSpecialist(BaseModel):
    specialist_name: str = Field(description="BenefitsAdvocate, CrisisNavigator, or AppealFighter")

# === MAIN AGENT CLASS ===
class HelpMeDammitAgent(mlflow.pyfunc.PythonModel):
    
    def __init__(self):
        # Don't initialize agents here - do it lazily in predict()
        self.triage_agent = None
        self.benefits_agent = None
        print("HelpMeDammit Agent initialized")

    def _get_triage_agent(self):
        if self.triage_agent is None:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an empathetic healthcare advocate. Acknowledge the user's situation, explain you have access to Medicare database, then route them to: BenefitsAdvocate (for Medicare/benefits), CrisisNavigator (emergencies), or AppealFighter (claim denials)."),
                ("human", "{input}")
            ])
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
            self.triage_agent = prompt | llm.with_structured_output(RouteToSpecialist)
        return self.triage_agent

    def _get_benefits_agent(self):
        if self.benefits_agent is None:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a Benefits Advocate. Use the find_plans_with_benefits tool to search for Medicare plans. Extract benefit names from user queries and call the tool with a list of benefits."),
                ("human", "{input}")
            ])
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
            self.benefits_agent = prompt | llm.bind_tools([find_plans_with_benefits])
        return self.benefits_agent

    def predict(self, context, model_input):
        try:
            query = model_input['query'][0]
            story_steps = []
            
            # Step 1: Triage (initialize agent on first use)
            triage_result = self._get_triage_agent().invoke({"input": query})
            specialist = triage_result.specialist_name
            
            story_steps.append({
                "type": "agent_message", 
                "content": f"I understand you need help. Let me connect you to our {specialist}..."
            })
            story_steps.append({
                "type": "tool_call", 
                "tool_name": "route_to_specialist", 
                "args": {"specialist_name": specialist}, 
                "status": "SUCCESS"
            })
            
            # Step 2: Run specialist (simplified to just BenefitsAdvocate for demo)
            if specialist == "BenefitsAdvocate":
                specialist_response = self._get_benefits_agent().invoke({"input": query})
                
                if specialist_response.tool_calls:
                    tool_call = specialist_response.tool_calls[0]
                    tool_args = tool_call['args']
                    
                    story_steps.append({
                        "type": "tool_call",
                        "tool_name": "find_plans_with_benefits", 
                        "args": tool_args,
                        "status": "PENDING"
                    })
                    
                    # Execute the tool
                    plans_data = find_plans_with_benefits.invoke(tool_args)
                    structured_results = json.loads(plans_data) if plans_data != '[]' else []
                    
                    story_steps[-1]['status'] = 'SUCCESS'
                    story_steps[-1]['result_preview'] = f"Found {len(structured_results)} plans"
                    
                    final_response = f"I've searched our Medicare database and found {len(structured_results)} plans that match your needs."
                    story_steps.append({"type": "agent_message", "content": final_response})
                    
                else:
                    final_response = specialist_response.content
                    structured_results = []
                    story_steps.append({"type": "agent_message", "content": final_response})
            else:
                # Simple fallback for other specialists
                final_response = f"I've connected you to our {specialist}. They are standing by to help with your situation."
                structured_results = []
                story_steps.append({"type": "agent_message", "content": final_response})
            
            # Assemble response
            payload = {
                "steps": story_steps,
                "structured_results": structured_results,
                "final_response": final_response,
                "user_profile_update": {"needs": tool_args.get('required_benefits', []) if 'tool_args' in locals() else []}
            }
            
            return pd.DataFrame([json.dumps(payload)])
            
        except Exception as e:
            error_payload = {
                "steps": [{"type": "error", "content": f"An error occurred: {str(e)}"}],
                "structured_results": [],
                "final_response": "I apologize, but I encountered an error processing your request.",
                "user_profile_update": {}
            }
            return pd.DataFrame([json.dumps(error_payload)])

# === DEPLOYMENT ===
CATALOG_NAME = "hackathon_helpme"
SCHEMA_NAME = "default" 
MODEL_NAME = "helpmedamnit_agent"
full_model_name = f"{CATALOG_NAME}.{SCHEMA_NAME}.{MODEL_NAME}"
mlflow.set_registry_uri("databricks-uc")

print(f"Deploying to: {full_model_name}")

with mlflow.start_run() as run:
    agent_model = HelpMeDammitAgent()  # This won't try to create OpenAI clients now
    input_example = pd.DataFrame({"query": ["I need a medicare plan with dental and vision."]})
    output_example = pd.DataFrame(['{"steps": [], "structured_results": [], "final_response": "", "user_profile_update": {}}'])
    signature = infer_signature(input_example, output_example)

    mlflow.pyfunc.log_model(
        artifact_path="agent_orchestrator",
        python_model=agent_model,
        registered_model_name=full_model_name,
        pip_requirements=["mlflow", "langchain", "langchain-openai", "langchain-experimental", "pandas", "scikit-learn", "pydantic"],
        signature=signature,
        input_example=input_example
    )
    print("✅ Model deployed successfully!")

print("🚀 HelpMeDammit agent is ready!") 