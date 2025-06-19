from agents.base_agent import BaseAgent

class ExportAgent:
    def __init__(self, model="mistral", temperature=0.3):
        self.agent = BaseAgent(
            name="ExportAgent",
            prompt="""
You are an expert assistant responsible for generating structured output files from agent chain results.

You will be given:
1. `chain_output`: the full result of an agent chain (text).
2. `user_export_prompt`: a user instruction like "Give me a Word summary" or "Output as an Excel table".

If the user wants Excel or CSV output, you MUST include:
- "columns": a list of column headers
- "rows": a list of lists (one row per record)

If the user wants a Word or PDF output, use:
- "title": document title
- "sections": a list of {"heading": ..., "body": ...}

Respond in this JSON format:
{
  "file_type": "excel" | "docx" | "pdf" | "txt",
  "filename": "myfile.ext",
  "content": { ... }
}
""",
            model=model,
            temperature=temperature
        )

    def run(self, chain_output: str, user_export_prompt: str) -> str:
        combined_input = f"""chain_output:
{chain_output}

user_export_prompt:
{user_export_prompt}
"""
        return self.agent.run(combined_input)
