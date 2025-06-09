import pandas as pd

# We now import agents directly, no MLflow wrapper involved for local testing.
from src.agents.triage import TriageAgent
from src.agents.crisis_navigator import CrisisNavigator
from src.agents.benefits_advocate import BenefitsAdvocate
from src.agents.appeal_fighter import AppealFighter

def run_local_agent_test():
    """
    Tests the core agent logic locally, without any data dependencies.
    """
    print("--- Running Local Agent Test ---")
    
    # Initialize agents directly
    crisis_navigator = CrisisNavigator()
    benefits_advocate = BenefitsAdvocate()
    appeal_fighter = AppealFighter()
    
    specialists = {
        "crisis_navigator": crisis_navigator,
        "benefits_advocate": benefits_advocate,
        "appeal_fighter": appeal_fighter,
    }
    triage_agent = TriageAgent(specialists=specialists)
    
    test_queries = [
        "I am in a crisis and need help now!",
        "My insurance denied my claim for a hospital stay.",
        "I want to appeal the decision from my provider.",
    ]
    
    print("\n--- Test Results ---")
    for query in test_queries:
        response = triage_agent.route(query)
        print(f"Query: '{query}'")
        print(f"Response: {response}\n")
        
    print("--- End of Local Agent Test ---")

if __name__ == "__main__":
    run_local_agent_test()
