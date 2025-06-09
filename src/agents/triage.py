class TriageAgent:
    def __init__(self, specialists: dict):
        self.specialists = specialists
        # In a real implementation, this would use an LLM to classify the query.
        # For this skeleton, we'll use simple keyword matching.

    def route(self, query: str) -> str:
        """
        Routes the user's query to the appropriate specialist agent.
        """
        print(f"Triage agent processing query: '{query}'")
        query_lower = query.lower()

        if "crisis" in query_lower or "emergency" in query_lower:
            return self.specialists["crisis_navigator"].run(query)
        elif "benefit" in query_lower or "insurance" in query_lower or "denied" in query_lower:
            return self.specialists["benefits_advocate"].run(query)
        elif "appeal" in query_lower or "fight" in query_lower:
            return self.specialists["appeal_fighter"].run(query)
        else:
            # Default fallback or a more sophisticated "access_finder" agent
            return "I'm not sure how to route your request. Could you be more specific? I can help with 'crisis', 'benefits', or 'appeals'."
