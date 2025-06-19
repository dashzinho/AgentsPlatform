# core/agent_chain.py
from core.agent_manager import load_agent
from agents.base_agent import BaseAgent

def sanitize_output(text):
    cleaner = BaseAgent(
        name="Sanitizer",
        prompt="""You are a text cleaner. Your job is to sanitize input text for export into Excel and PDF. 
Make sure the text contains no emojis, no smart quotes, no special symbols like €, and no non-printable characters.
Replace € with EUR, remove emojis, and correct any formatting artifacts. Return the cleaned version only.""",
        model="mistral",  # or llama3 etc
        temperature=0
    )
    return cleaner.run(text)

def run_agent_chain(user_input, agents, pass_context=True):
    steps = []
    context = ""
    last_output = ""

    for i, agent in enumerate(agents):
        input_to_agent = f"{context}\n{user_input}" if pass_context and context else user_input

        try:
            output = agent.run(input_to_agent)
        except Exception as e:
            output = f"[ERROR in agent '{agent.name}']: {e}"

        steps.append({
            "agent": agent.name,
            "input": input_to_agent,
            "output": output
        })

        context = output  # Used as context for next step
        last_output = output  # Save last output for Excel layout processing

    return steps, last_output  # last_output is now layout-aware
