"""
The main orchestrator for the HelpMeDammit multi-agent system.
"""
import mlflow
import pandas as pd
import json
from langchain_core.runnables import Runnable

# Import agent constructors
from agents.empathetic_triage import get_empathetic_triage_agent, RouteToSpecialist
from agents.benefits_advocate import get_benefits_advocate_agent

class HelpMeDammitAgent(mlflow.pyfunc.PythonModel):
    
    def __init__(self):
        self.empathetic_triage_agent = get_empathetic_triage_agent()
        self.specialist_agents = {
            "BenefitsAdvocate": get_benefits_advocate_agent()
            # NOTE: Other specialists would be added here
            # "CrisisNavigator": get_crisis_navigator_agent(),
            # "AppealFighter": get_appeal_fighter_agent(),
        }
        print("HelpMeDammitAgent initialized with all agents.")

    def _execute_tool_call(self, tool_call, tools_map):
        """A helper to execute a tool call."""
        tool_name = tool_call.tool
        tool_args = tool_call.tool_input
        if tool_name in tools_map:
            return tools_map[tool_name].invoke(tool_args)
        else:
            return f"Error: Tool '{tool_name}' not found."

    def predict(self, context, model_input):
        """
        The main prediction method that orchestrates the agent chain.
        """
        query = model_input['query'][0]
        
        # This list will store the "story" of the interaction for the frontend
        story_steps = []

        # Step 1: Run the Empathetic Triage Agent
        triage_result = self.empathetic_triage_agent.invoke({"input": query})
        
        # The triage agent's "result" is actually a tool call to route the user
        # We capture the empathetic message and the routing decision
        story_steps.append({"type": "agent_message", "content": triage_result.content})
        
        if not triage_result.tool_calls:
            # Fallback if the agent doesn't use the tool
            story_steps.append({"type": "error", "content": "Triage agent failed to select a specialist."})
            return json.dumps({"steps": story_steps, "final_response": "I'm sorry, I was unable to determine the right specialist for your query."})

        # Extract the routing decision
        routing_call = triage_result.tool_calls[0]
        specialist_name = routing_call['args']['specialist_name']
        story_steps.append({"type": "tool_call", "tool_name": "route_to_specialist", "args": routing_call['args'], "status": "SUCCESS"})
        
        # Step 2: Route to the selected Specialist Agent
        if specialist_name not in self.specialist_agents:
            story_steps.append({"type": "error", "content": f"Specialist '{specialist_name}' not found."})
            return json.dumps({"steps": story_steps, "final_response": f"I'm sorry, the {specialist_name} specialist is not available."})
            
        specialist_agent, specialist_tools = self.specialist_agents[specialist_name]
        tools_map = {tool.name: tool for tool in specialist_tools}

        # Step 3: Run the Specialist Agent
        story_steps.append({"type": "agent_message", "content": f"Connecting you to the {specialist_name}..."})
        specialist_response = specialist_agent.invoke({"input": query})

        # Step 4: Handle the Specialist's response and potential tool calls
        final_response_text = ""
        structured_results = None

        if not specialist_response.tool_calls:
            # The agent responded directly without using a tool
            final_response_text = specialist_response.content
            story_steps.append({"type": "agent_message", "content": final_response_text})
        else:
            # The agent needs to use a tool (e.g., query the database)
            tool_call = specialist_response.tool_calls[0]
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            story_steps.append({"type": "tool_call", "tool_name": tool_name, "args": tool_args, "status": "PENDING"})

            # Execute the tool
            tool_output_json = self._execute_tool_call(tool_call, tools_map)
            structured_results = json.loads(tool_output_json) # The tool returns JSON
            story_steps[-1]['status'] = 'SUCCESS' # Update the last step status
            story_steps[-1]['result_preview'] = f"Found {len(structured_results)} plans."

            # We would typically feed the result back into the agent for a final summary,
            # but for the hackathon, we can create a canned response for the demo.
            final_response_text = f"I've analyzed the Medicare database for plans with the benefits you requested. Here are the results I found."
            story_steps.append({"type": "agent_message", "content": final_response_text})

        # Assemble the final JSON payload for the frontend
        final_payload = {
            "steps": story_steps,
            "structured_results": structured_results,
            "final_response": final_response_text,
            # In a real app, the agent would also determine the profile update
            "user_profile_update": {"needs": tool_args.get('required_benefits', []) if 'tool_args' in locals() else []}
        }

        # Return as a JSON string in a pandas DataFrame, as expected by mlflow.pyfunc
        return pd.DataFrame([json.dumps(final_payload)])

