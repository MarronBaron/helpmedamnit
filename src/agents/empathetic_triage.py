"""
The Empathetic Triage Agent.

This agent is the first point of contact for the user. Its goals are:
1.  To be empathetic and acknowledge the user's situation.
2.  To clearly state its capabilities and the data it has access to.
3.  To use a tool to route the user's query to the correct specialist agent.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI

# Define the tools
class RouteToSpecialist(BaseModel):
    """Routes the user's query to the most appropriate specialist agent."""
    specialist_name: str = Field(description="The name of the specialist agent to route to. Should be one of: 'BenefitsAdvocate', 'CrisisNavigator', 'AppealFighter'.",)
    
# System prompt for the agent
SYSTEM_PROMPT = """You are the first point of contact for "HelpMeDammit," an AI assistant for healthcare advocacy. 
Your primary role is to be empathetic, understand the user's problem, and route them to the correct specialist.

First, provide a brief, empathetic acknowledgment of the user's situation.
Next, briefly explain the kinds of help you can provide. Mention that you have access to a real-time Medicare benefits database to find specific plans.
Finally, based on the user's query, you MUST use the `RouteToSpecialist` tool to direct the user to the correct specialist agent.

Available Specialists:
- 'CrisisNavigator': For users in immediate medical or mental health crises.
- 'BenefitsAdvocate': For users asking about Medicare, insurance benefits, finding plans, or costs.
- 'AppealFighter': For users who have had a claim denied and want to appeal.

Always use the tool. Do not attempt to answer the user's question directly.
"""

def get_empathetic_triage_agent():
    """Builds and returns the Empathetic Triage Agent."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
        ]
    )
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    agent = prompt | llm.with_structured_output(RouteToSpecialist)
    return agent 