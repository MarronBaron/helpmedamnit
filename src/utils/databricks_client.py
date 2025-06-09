import os
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient

def get_db_client():
    """
    Initializes and returns a Databricks WorkspaceClient.

    This function loads environment variables from a .env file,
    and uses them to configure the WorkspaceClient.

    Returns:
        WorkspaceClient: An authenticated Databricks WorkspaceClient object.
    
    Raises:
        ValueError: If DATABRICKS_HOST or DATABRICKS_TOKEN are not set.
    """
    load_dotenv()

    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")

    if not host or not token:
        raise ValueError("DATABRICKS_HOST and DATABRICKS_TOKEN must be set in your .env file.")

    return WorkspaceClient(host=host, token=token)

if __name__ == '__main__':
    # This block allows you to verify the connection by running the file directly:
    # python src/utils/databricks_client.py
    print("Attempting to connect to Databricks...")
    try:
        client = get_db_client()
        # A simple command to verify the connection is working
        catalogs = list(client.catalogs.list())
        print("✅ Successfully connected to Databricks!")
        print(f"Found {len(catalogs)} catalogs in your workspace.")
        # For example, let's print the first 5 catalog names
        for catalog in catalogs[:5]:
            print(f"  - {catalog.name}")
    except Exception as e:
        print(f"❌ Failed to connect to Databricks: {e}")
