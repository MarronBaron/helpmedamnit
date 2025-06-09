# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Deploy HelpMeDammit Agent to Model Registry
# MAGIC 
# MAGIC This notebook packages our multi-agent system and registers it as a new version in the MLflow Model Registry.
# MAGIC The registered model can then be deployed to a Model Serving Endpoint.

# COMMAND ----------

# MAGIC %pip install mlflow langchain langchain-openai langchain-experimental
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import mlflow
import os
import shutil
from src.main import HelpMeDammitAgent

# Define names for the model and catalog
CATALOG_NAME = "hackathon_helpme"
SCHEMA_NAME = "default"
MODEL_NAME = "helpmedamnit_agent"
mlflow.set_registry_uri("databricks-uc")
full_model_name = f"{CATALOG_NAME}.{SCHEMA_NAME}.{MODEL_NAME}"

# COMMAND ----------

# Create a temporary directory to copy the src code to
# This ensures that all agent code is packaged with the model
temp_code_path = "/tmp/helpmedamnit_src"
local_code_path = "src" # Relative path to your src folder from the notebook

# Get the absolute path of the notebook to find the repo root
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
repo_root = os.path.dirname(os.path.dirname(notebook_path))
source_code_path = os.path.join(repo_root, local_code_path)

if os.path.exists(temp_code_path):
    shutil.rmtree(temp_code_path)
shutil.copytree(source_code_path, temp_code_path)

code_path_dict = {"src": temp_code_path}

# COMMAND ----------

# Log the model to the registry
with mlflow.start_run():
    mlflow.pyfunc.log_model(
        artifact_path="agent_orchestrator",
        python_model=HelpMeDammitAgent(),
        code_path=list(code_path_dict.values()),
        registered_model_name=full_model_name,
        pip_requirements=[
            "mlflow",
            "langchain",
            "langchain-openai",
            "langchain-experimental",
            "pydantic",
            "pandas",
            "scikit-learn"
        ],
        input_example={"query": "I need a medicare plan with dental."}
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deployment Instructions
# MAGIC 
# MAGIC 1.  **Run this notebook** to register the latest version of the model.
# MAGIC 2.  Navigate to the **Serving** section in the left-hand menu of Databricks.
# MAGIC 3.  Find your existing `helpmedamnit-endpoint`.
# MAGIC 4.  Click **Edit endpoint**.
# MAGIC 5.  Under "Served models," find the `helpmedamnit_agent` and select the **newest version** that you just registered.
# MAGIC 6.  Click **Update** and wait for the new version to deploy. The status will change to "Ready".
# MAGIC 7.  Your awesome new agent is now live! 