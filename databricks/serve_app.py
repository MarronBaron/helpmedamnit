import streamlit as st
import pandas as pd
import mlflow

# This is the name of the model as it will be registered in MLflow Model Registry
# We will register it in the deploy_model.py script later.
REGISTERED_MODEL_NAME = "databricksday.default.helpmedamnit_agent"

def get_latest_model_version(model_name):
    """
    Gets the latest version of a registered model from the MLflow Model Registry.
    """
    client = mlflow.tracking.MlflowClient()
    versions = client.get_latest_versions(model_name, stages=["Production"])
    if not versions:
        raise ValueError(f"No 'Production' version found for model '{model_name}'.")
    return versions[0].version

def run_app():
    """
    The main function for the Streamlit application.
    """
    st.title("🆘 HelpMeDammit - AI Advocate")
    st.markdown(
        "This is an agentic AI advocacy system that steps in for those that can't help themselves. "
        "Describe your problem below, and the agent will take action on your behalf."
    )

    # This will run on Databricks, so we assume we can load the model from the registry.
    try:
        # Load the MLflow model from the Model Registry
        # This assumes you have run deploy_model.py to register a "Production" version
        latest_version = get_latest_model_version(REGISTERED_MODEL_NAME)
        model_uri = f"models:/{REGISTERED_MODEL_NAME}/{latest_version}"
        model = mlflow.pyfunc.load_model(model_uri)

        st.success(f"Successfully loaded agent model '{REGISTERED_MODEL_NAME}' version {latest_version}.")

        # User input
        user_query = st.text_input("How can I help you today?", "e.g., My insurance denied my appeal.")

        if st.button("Get Help"):
            if user_query:
                with st.spinner("Agent is thinking..."):
                    # The model expects a pandas DataFrame
                    model_input = pd.DataFrame({"query": [user_query]})
                    result = model.predict(model_input)
                    response = result["response"].iloc[0]
                    
                    st.markdown("### Agent Response:")
                    st.write(response)
            else:
                st.warning("Please enter a query.")

    except Exception as e:
        st.error(f"Failed to load or run the agent model: {e}")
        st.info("Please make sure you have registered a 'Production' version of the model using the 'deploy_model.py' script.")


if __name__ == "__main__":
    # NOTE: This Streamlit app is designed to be run within a Databricks App,
    # which provides the necessary environment and authentication.
    # Running it locally will likely fail unless you have MLflow configured
    # to track to a Databricks server.
    run_app()
