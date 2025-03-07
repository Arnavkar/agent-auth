from browser_use.agent.views import AgentState
from browser_use.browser.browser import Browser, BrowserConfig
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from browser_use import Agent
from browser_use.agent.views import ActionResult
from browser_use.controller.service import Controller
from pydantic import BaseModel
import json
import os

load_dotenv()

agent_state = AgentState()

class TaskOutput(BaseModel):
    task_status: str
    execution_time: str
    completed_at: str
    summary: str
    user_provided_data: dict
    
class CustomController(Controller):
    def __init__(self, output_model):
        super().__init__(output_model=output_model)
        self._register_custom_actions()
        
    def _register_custom_actions(self):
        @self.registry.action("Ask user for more information")
        async def ask_user_for_info(message: str):
            global agent_state
            agent_state.paused = True
            response = input(f"Agent: {message} \n Your response: \n")
            agent_state.paused = False
            return ActionResult(extracted_content=response)
        
def get_last_run_data(path):
    last_run_file = 'run_data.json'
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

async def main(task, max_steps=20):
    global agent_state
            
    task += '''\n 
    Additiona Instructions: 
    When reaching any kind of login screen or auth screen - always ask the user for their login credentials (username and password), UNLESS the user has already provided in a previous run
    NEVER ASK THE USER FOR THEIR PASSWORD TWICE
    If MFA via a code is required, ask the user for their code.
    If MFA via a push notification is required, ask the USER to send YES or NO, depending on whether they approve the login.
    
    If you hit an unxpected modal - close it and continue with the task.
    
    Never return an error unless the page you are on is a 404 page or the user has provided an incorrect URL - otherwise just keep executing till the last step and return the status of the task.
    '''
    
    run_data = get_last_run_data(os.getcwd())
    if run_data:
        task += "\n Additonal data from the last run: \n {}".format(run_data)

    browser = Browser(
         config=BrowserConfig(
            headless=False,
         )
    )
    
    initial_actions = [
        {'open_tab': {'url': 'https://www.google.com'}}
    ]
    
    browser_context = await browser.new_context()
 
    agent = Agent(
        task=task,
        initial_actions=initial_actions,
        llm=ChatOpenAI(model='gpt-4o-mini'),
        browser=browser,
        browser_context=browser_context,
        injected_agent_state=agent_state,
        controller=CustomController(output_model=TaskOutput)
    )
    
    history = await agent.run(max_steps=max_steps)
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
            serialized = agent_state.model_dump_json(exclude=["screenshot"])
            f.write(serialized)
            
    return result

if __name__ == '__main__':
    task = input("Type in your task: \n")
    result = asyncio.run(main(task))
    print(result)
    exit()