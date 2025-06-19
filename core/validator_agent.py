from agents.base_agent import BaseAgent
import os

class ValidatorAgent:
    def __init__(self, model="mistral", temperature=0.4):
        self.agent = BaseAgent(
            name="ValidatorAgent",
            model=model,
            temperature=temperature,
            prompt="""
You're a validation assistant. You will receive an error message from a failed file generation attempt.
Your task is to rewrite a better, more precise prompt for the export agent to help it succeed.

Example:
Input error: "KeyError: 'rows'"
User prompt: "Output an Excel table"

Your response:
"Generate an Excel file with two columns: 'Field' and 'Value', and provide sample rows if not available."
"""
        )

    def generate_new_prompt(self, user_prompt, fallback_error):
        full_input = f"""Input error:\n{fallback_error}\n\nOriginal user prompt:\n{user_prompt}"""
        return self.agent.run(full_input)