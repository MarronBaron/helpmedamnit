import pandas as pd
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import Disposition
import os

def load_benefits_data(catalog: str, schema: str, table: str) -> pd.DataFrame:
    """
    Connects to Databricks via the SDK and loads a specified table as a pandas DataFrame.
    """
    print(f"Attempting to load data from {catalog}.{schema}.{table} via SDK...")
    try:
        host = os.getenv("DATABRICKS_HOST")
        token = os.getenv("DATABRICKS_TOKEN")
        if not host or not token:
            raise ValueError("DATABRICKS_HOST and DATABRICKS_TOKEN must be set.")
            
        w = WorkspaceClient(host=host, token=token)

        # To run a query, we need a running SQL warehouse.
        # This code finds the first available running warehouse.
        warehouse_id = None
        for wh in w.warehouses.list():
            if wh.state == "RUNNING":
                warehouse_id = wh.id
                break
        
        if not warehouse_id:
            raise Exception("No running SQL warehouse found in your Databricks workspace.")

        print(f"Found and using warehouse ID: {warehouse_id}")

        stmt = f"SELECT * FROM {catalog}.{schema}.{table}"
        
        # This executes the query and waits for it to finish.
        wait_resp = w.statement_execution.execute_statement(
            statement=stmt,
            warehouse_id=warehouse_id,
            disposition=Disposition.INLINE,
            wait_timeout='50s'
        )

        # The SDK returns data in Apache Arrow format, which we convert to pandas.
        arrow_table = w.statement_execution.fetch_result(
            statement_id=wait_resp.statement_id
        ).result.data
        
        df = arrow_table.to_pandas()
        
        print(f"✅ Successfully loaded {len(df)} records from {table} using the SDK.")
        return df
        
    except Exception as e:
        print(f"❌ Failed to load data from Databricks using the SDK: {e}")
        return pd.DataFrame()

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    # Make sure your .env file is configured for this to work locally.
    benefits_df = load_benefits_data(catalog="databricksday", schema="default", table="benefits")
    
    if not benefits_df.empty:
        print("\n--- Sample Data ---")
        print(benefits_df.head())
