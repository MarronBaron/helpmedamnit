// This is the Vercel serverless function that will act as our secure proxy
export default async function handler(req, res) {
  // Ensure we're only handling POST requests
  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    return res.status(405).end(`Method ${req.method} Not Allowed`);
  }

  try {
    const { query } = req.body;
    const databricksToken = process.env.DATABRICKS_TOKEN;
    const databricksEndpoint = "https://dbc-1a3c0609-0df4.cloud.databricks.com/serving-endpoints/helpmedamnit-endpoint/invocations";

    if (!databricksToken) {
      return res.status(500).json({ error: 'Databricks API token is not configured on the server.' });
    }

    const response = await fetch(databricksEndpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${databricksToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ inputs: { query: [query] } })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Databricks API error: ${response.status} - ${errorText}`);
      throw new Error(`Databricks API responded with status: ${response.status}`);
    }

    const databricksData = await response.json();
    
    // The model returns a JSON string in predictions[0]
    // We need to return it as the 'response' field for the frontend
    const agentJsonString = databricksData.predictions[0];
    
    // Send the JSON string as the response field
    res.status(200).json({ response: agentJsonString });

  } catch (error) {
    console.error("Error in serverless function:", error);
    res.status(500).json({ error: `An error occurred while contacting the Databricks endpoint: ${error.message}` });
  }
} 