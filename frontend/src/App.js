import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';

// Custom SOS Icon Component
const SOSIcon = () => (
  <div className="sos-icon">
    <div className="sos-text">SOS</div>
  </div>
);

function App() {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [agentSteps, setAgentSteps] = useState([]);
  const [structuredResults, setStructuredResults] = useState([]);
  const [finalResponse, setFinalResponse] = useState('');
  const [userProfile, setUserProfile] = useState({ needs: [] });
  const [showProfile, setShowProfile] = useState(false);

  // Load user profile from localStorage on component mount
  useEffect(() => {
    const savedProfile = localStorage.getItem('helpmedamnit_profile');
    if (savedProfile) {
      setUserProfile(JSON.parse(savedProfile));
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setAgentSteps([]);
    setStructuredResults([]);
    setFinalResponse('');

    try {
      const apiResponse = await axios.post('/api/invoke', { query });
      
      // Debug: Log what we're actually receiving
      console.log('API Response:', apiResponse.data);
      console.log('Response type:', typeof apiResponse.data.response);
      console.log('Response value:', apiResponse.data.response);
      
      // Try to parse the response - handle both string and object cases
      let data;
      if (typeof apiResponse.data.response === 'string') {
        data = JSON.parse(apiResponse.data.response);
      } else {
        // Already an object
        data = apiResponse.data.response;
      }
      
      // Animate through the steps
      setAgentSteps(data.steps || []);
      setStructuredResults(data.structured_results || []);
      setFinalResponse(data.final_response || 'Response received.');
      
      // Update user profile
      if (data.user_profile_update) {
        const updatedProfile = { ...userProfile, ...data.user_profile_update };
        setUserProfile(updatedProfile);
        localStorage.setItem('helpmedamnit_profile', JSON.stringify(updatedProfile));
      }

    } catch (err) {
      console.error('Full error:', err);
      setError('Failed to get a response from the agent.');
    } finally {
      setIsLoading(false);
    }
  };

  const clearProfile = () => {
    setUserProfile({ needs: [] });
    localStorage.removeItem('helpmedamnit_profile');
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="title-container">
          <SOSIcon />
          <h1>HelpMeDammit</h1>
        </div>
        <p>Your AI advocate for navigating healthcare bureaucracy.</p>
        <button 
          className="profile-toggle"
          onClick={() => setShowProfile(!showProfile)}
        >
          Profile {userProfile.needs.length > 0 && `(${userProfile.needs.length} needs)`}
        </button>
      </header>

      <AnimatePresence>
        {showProfile && (
          <motion.div 
            className="user-profile"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <h3>Your Profile</h3>
            <div className="profile-content">
              {userProfile.needs.length > 0 ? (
                <div>
                  <p><strong>Identified Needs:</strong></p>
                  <div className="needs-tags">
                    {userProfile.needs.map((need, i) => (
                      <span key={i} className="need-tag">{need}</span>
                    ))}
                  </div>
                </div>
              ) : (
                <p>No needs identified yet. Ask about Medicare benefits to get started!</p>
              )}
              <button onClick={clearProfile} className="clear-btn">Clear Profile</button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <main>
        <form onSubmit={handleSubmit}>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Describe your problem... e.g., 'I need a Medicare plan with dental and transportation benefits.'"
            rows="4"
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Agent is thinking...' : 'Get Help'}
          </button>
        </form>

        {error && <div className="error">{error}</div>}

        {/* Animated Agent Steps */}
        <AnimatePresence>
          {agentSteps.length > 0 && (
            <motion.div 
              className="agent-thinking"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <h2>🤖 Agent Activity</h2>
              {agentSteps.map((step, index) => (
                <motion.div
                  key={index}
                  className={`step step-${step.type}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.5 }}
                >
                  {step.type === 'agent_message' && (
                    <div className="agent-message">
                      <span className="step-icon">💬</span>
                      <p>{step.content}</p>
                    </div>
                  )}
                  
                  {step.type === 'tool_call' && (
                    <div className="tool-call">
                      <span className="step-icon">🔧</span>
                      <div>
                        <p><strong>Tool:</strong> {step.tool_name}</p>
                        <p><strong>Status:</strong> 
                          <span className={`status ${step.status?.toLowerCase()}`}>
                            {step.status}
                          </span>
                        </p>
                        {step.result_preview && (
                          <p><strong>Result:</strong> {step.result_preview}</p>
                        )}
                      </div>
                    </div>
                  )}
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Structured Results */}
        <AnimatePresence>
          {structuredResults.length > 0 && (
            <motion.div 
              className="structured-results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: agentSteps.length * 0.5 + 0.5 }}
            >
              <h2>📋 Medicare Plans Found</h2>
              <div className="results-grid">
                {structuredResults.map((result, index) => (
                  <motion.div
                    key={index}
                    className="result-card"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.1 * index }}
                  >
                    <h3>Plan {result.pbp_a_plan_identifier}</h3>
                    <p><strong>Plan Number:</strong> {result.pbp_a_hnumber}</p>
                    <p><strong>Benefits:</strong> {result.all_benefits}</p>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Final Response */}
        <AnimatePresence>
          {finalResponse && (
            <motion.div 
              className="final-response"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: (agentSteps.length * 0.5) + (structuredResults.length * 0.1) + 1 }}
            >
              <h2>✨ Summary</h2>
              <p>{finalResponse}</p>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;
