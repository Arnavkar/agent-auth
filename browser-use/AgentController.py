from langchain_openai import ChatOpenAI
from browser_use import Agent
import asyncio

class AgentController:
    def __init__(self):
        self.running = False
        
    def initialize_agent(self, task: str):
        self.agent = Agent(
            task=task,
            llm=ChatOpenAI(model='gpt-4o-mini')
        )

    async def run_agent(self):
        self.running = True
        await self.agent.run()

    def start(self):
        asyncio.run(self.run_agent())

    def pause(self):
        self.agent.pause()

    def resume(self):
        self.agent.resume()

    def stop(self):
        self.agent.stop()
        self.running = False