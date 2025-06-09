import mlflow
import pandas as pd
from mlflow.models.signature import infer_signature

# Adjusting imports for the new location
from src.agents.triage import TriageAgent
from src.agents.crisis_navigator import CrisisNavigator
from src.agents.benefits_advocate import BenefitsAdvocate
from src.agents.appeal_fighter import AppealFighter

class AdvocateAgentWrapper(mlflow.pyfunc.PythonModel):
    """
    An MLflow wrapper for the HelpMeDammit multi-agent system.
    This is intended to be run ON Databricks, not locally.
    """

    def load_context(self, context):
        """
        This method is called when the model is loaded on Databricks.
        """
        print("Loading agent context on Databricks...")

        # Initialize specialist agents
        self.crisis_navigator = CrisisNavigator()
        self.benefits_advocate = BenefitsAdvocate()
        self.appeal_fighter = AppealFighter()
        
        specialists = {
            "crisis_navigator": self.crisis_navigator,
            "benefits_advocate": self.benefits_advocate,
            "appeal_fighter": self.appeal_fighter,
        }
        self.triage_agent = TriageAgent(specialists=specialists)
        print("✅ Agent context loaded successfully on Databricks.")

    def predict(self, context, model_input):
        """
        This is the main entry point for the served model.
        """
        queries = model_input["query"]
        responses = []
        for query in queries:
            response = self.triage_agent.route(query)
            responses.append(response)
            
        return pd.DataFrame({"response": responses})

# TODO: Add MLflow logging and registration code here
# For example:
# with mlflow.start_run() as run:
#     mlflow.pyfunc.log_model(
#         "helpmedamnit_agent",
#         python_model=AdvocateAgentWrapper(),
#         ...
#     )

def deploy():
    """
    Logs the AdvocateAgentWrapper to the MLflow Model Registry.
    This function is intended to be run from a Databricks environment.
    """
    # Create the catalog and schema if they don't exist
    print("Creating hackathon catalog...")
    spark.sql("CREATE CATALOG IF NOT EXISTS hackathon_helpme")
    spark.sql("CREATE SCHEMA IF NOT EXISTS hackathon_helpme.default")
    print("✅ Catalog and schema ready!")
    
    # This is the name your model will have in the Unity Catalog
    model_name = "hackathon_helpme.default.helpmedamnit_agent"
    
    print(f"Starting deployment for model: {model_name}")
    
    # It's good practice to set the experiment to keep runs organized
    user_name = dbutils.notebook.entry_point.getDbutils().notebook().getContext().userName().get()
    mlflow.set_experiment(f"/Users/{user_name}/helpmedamnit_experiment")

    with mlflow.start_run() as run:
        print(f"MLflow run started (run_id={run.info.run_id})...")
        
        # Create example input and output for signature inference
        example_input = pd.DataFrame({"query": ["I need Medicare plans with dental and fitness benefits"]})
        wrapper = AdvocateAgentWrapper()
        wrapper.load_context(None)
        example_output = wrapper.predict(None, example_input)
        
        # Infer the signature
        signature = infer_signature(example_input, example_output)
        
        # Log the model
        mlflow.pyfunc.log_model(
            artifact_path="agent_model",
            python_model=AdvocateAgentWrapper(),
            registered_model_name=model_name,
            signature=signature,
            input_example=example_input
        )
        
        print("✅ Model logged successfully.")

    print(f"🚀 Deployment complete! Model '{model_name}' is registered in the MLflow Model Registry.")


if __name__ == "__main__":
    # This script is designed to be run in a Databricks notebook or job.
    # The `dbutils` library is only available in that context.
    try:
        from pyspark.dbutils import DBUtils
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
        dbutils = DBUtils(spark)
        
        deploy()
        
    except ImportError:
        print("This script must be run in a Databricks environment (notebook or job) to access dbutils.")
        print("Skipping deployment.")
