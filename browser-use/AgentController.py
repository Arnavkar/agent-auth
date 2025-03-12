from browser_use.agent.views import AgentState
from browser_use.browser.browser import Browser, BrowserConfig
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from browser_use import Agent
from browser_use.agent.views import ActionResult
from browser_use.controller.service import Controller
from models import *
from cryptography.fernet import Fernet
import json
import os

class AgentController:
    def __init__(self):
        self.agent_state = AgentState()
        self.agent_spec = AgentSpec(
            key = Fernet.generate_key()
        )
        self.controller = Controller(output_model=TaskOutput)
        self.browser = Browser(
            config=BrowserConfig(
                headless=False,
            )
        )
        self.agent = None
        
    def register_ask_user(self, get_response_callback):
        @self.controller.action("Ask user for more information")
        async def ask_user_for_info(agent_message: str):
            self.agent_state.paused = True
            print("Agent paused")
            response = await get_response_callback(agent_message)
            self.agent_state.paused = False
            print("agent resumed")
            return ActionResult(extracted_content=response)
        
    # def register_status_update(self, status_update_callback):
    #     @self.controller.action("Provide a Status update")
    #     async def provide_status_update(message: str):
    #         status_update_callback(message)
    #         return ActionResult()

    def get_last_run_data(self,path):
        last_run_file = '/jobs/run_data.json'
        if os.path.exists(os.path.join(path, last_run_file)):
            with open(last_run_file, 'r') as f:
                try:
                    last_run_data = json.load(f)
                except json.JSONDecodeError:
                    print("Error decoding JSON from last_run.json.")
        else:
            last_run_data = None
            print("No last_run.json file found.")
        return last_run_data
    
    def get_last_step(self):
        return self.agent_state.last_result
    
    async def initialize_agent(self, task, llm:Models=Models.GPT_4o):
        task += '''\n 
        Additional Instructions:         
        When reaching any kind of login screen or auth screen - always ask the user for their login credentials UNLESS the user has already provided in a previous run. If the credentials do not work - ask again
        NEVER ASK THE USER FOR THEIR PASSWORD TWICE
        If MFA via a code is required, ask the user for their code.
        If MFA via a push notification is required, ask the USER to send YES or NO, depending on whether they approve the login.
        
        If you hit an unxpected modal - close it and continue with the task.
        
        Never return an error unless the page you are on is a 404 page or the user has provided an incorrect URL - otherwise just keep executing till the last step and return the status of the task.
        '''
        
        run_data = self.get_last_run_data(os.getcwd())
        if run_data:
            task += "\n Additonal data from the last run: \n {}".format(run_data)
        
        browser_context = await self.browser.new_context()
        initial_actions = [{'open_tab': {'url': 'https://www.google.com/'}}]
        
        self.agent = Agent(
            task=task,
            initial_actions=initial_actions,
            llm=ChatOpenAI(model=llm.value),
            browser=self.browser,
            browser_context=browser_context,
            injected_agent_state=self.agent_state,
            controller = self.controller,
            use_vision=True,
            planner_interval=5
        )
        
    async def run_task(self, max_steps=30):
        history = await self.agent.run(max_steps=max_steps)
        
        result = history.final_result()
        if result:
            parsed: TaskOutput = TaskOutput.model_validate_json(result)
            print('\n--------------------------------')
            print(f'Task status: {parsed.task_status}')
            print(f'Execution time: {parsed.execution_time}')
            print(f'Completed at: {parsed.completed_at}')
            print(f'Summary: {parsed.summary}')
            print(f'User provided data: {parsed.user_provided_data}')
            
            with open('task_output.json', 'w') as f:
                serialized = parsed.model_dump_json()
                f.write(serialized)

        else:
            print('No result')
            
        with open('agent_state.json', 'w') as f:
                serialized = self.agent_state.model_dump_json(exclude=["screenshot"])
                f.write(serialized)
                
        return result
    
    async def cancel_run(self):
        await self.agent.stop()
    
async def test():
    agent_controller = AgentController()
    agent_controller.register_ask_user(lambda x: input(f"AGENT: {x}\nUSER: "))
    await agent_controller.initialize_agent("Log into acorns", Models.GPT_4o_mini)
    await agent_controller.run_task()
    
if __name__ == "__main__":
    load_dotenv()
    asyncio.run(test())