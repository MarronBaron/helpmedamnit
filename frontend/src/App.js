import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setResponse('');

    try {
      // We now call our own backend API route, which will handle the Databricks call securely.
      const apiResponse = await axios.post('/api/invoke', { query });
      
      setResponse(apiResponse.data.response);

    } catch (err) {
      setError('Failed to get a response from the agent.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🆘 HelpMeDammit</h1>
        <p>Your AI advocate for navigating healthcare bureaucracy.</p>
      </header>
      <main>
        <form onSubmit={handleSubmit}>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Describe your problem here... e.g., 'I need a Medicare plan with dental and transportation benefits.'"
            rows="4"
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Agent is thinking...' : 'Get Help'}
          </button>
        </form>
        {error && <div className="error">{error}</div>}
        {response && (
          <div className="response-container">
            <h2>Agent's Response:</h2>
            <pre>{response}</pre>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
