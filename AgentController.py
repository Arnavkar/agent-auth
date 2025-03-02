from langchain_openai import ChatOpenAI
from browser_use import Agent
from CustomController import CustomController
import asyncio

agent_event_loop = None
user_response_future = None

class CustomController(Controller):
    def __init__(self, exclude_actions: list[str] = [],
                 output_model: Optional[Type[BaseModel]] = None
                 ):
        super().__init__(exclude_actions=exclude_actions, output_model=output_model)
        self._register_custom_actions()

    def _register_custom_actions(self):
        @self.registry.action("Ask user for more information")
        async def ask_user_for_info(message: str):
            global user_response_future, agent_event_loop
            # Create a new future on the agent's event loop.
            user_response_future = agent_event_loop.create_future()
            print("Agent is asking:", message)
            # Wait until the future is resolved by the UI.
            response = await user_response_future
            print("Received answer from UI:", response)
            return ActionResult(extracted_content=response)

class AgentController:
    def __init__(self):
        self.running = False
        
    def initialize_agent(self, task, llm):
        controller = CustomController()
        self.agent = Agent(
			task=task, 
			llm=ChatOpenAI(model=llm), 
			controller=controller
		)
    
    async def run_agent(self):
        self.running = True
        await self.agent.run()

    def start(self, task, llm):
        global agent_event_loop
        agent_event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(agent_event_loop)
        agent_event_loop.run_until_complete(self.run_agent())

    def pause(self):
        self.agent.pause()

    def resume(self):
        self.agent.resume()

    def stop(self):
        self.agent.stop()
        self.running = False

    def get_thread_loop(self):
        return asyncio.get_event_loop()
