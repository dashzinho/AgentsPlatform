from langchain_community.chat_models import ChatOllama
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage, HumanMessage

class BaseAgent:
    def __init__(self, name, prompt, model="mistral", temperature=0.7, response_format=None):
        self.name = name
        self.prompt = prompt
        self.model = model
        self.temperature = temperature
        self.response_format = response_format
        self.llm = ChatOllama(model=model, temperature=temperature)
        self.memory = ConversationBufferMemory(return_messages=True)

    def run(self, user_input):
        prompt = self.prompt
        if self.response_format:
            prompt += f"\n\nPlease respond in the following JSON format:\n{self.response_format}"
        messages = [SystemMessage(content=prompt)] + self.memory.chat_memory.messages
        messages.append(HumanMessage(content=user_input))

        response = self.llm(messages).content
        self.memory.chat_memory.add_user_message(user_input)
        self.memory.chat_memory.add_ai_message(response)
        return response