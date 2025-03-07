import asyncio
import threading
import gradio as gr
from typing import Optional, Type
from pydantic import BaseModel
# Import your agent and controller libraries
from langchain_openai import ChatOpenAI
from browser_use import Agent, Agent
from browser_use.agent.views import ActionResult, AgentState
from browser_use.controller.service import Controller

# Global variables to hold the agent's event loop and current user response future

class CustomController(Controller):
    def __init__(self):
        super().__init__()
        self._register_custom_actions()
        
    def _register_custom_actions(self):
        @self.registry.action("Ask user for more information")
        async def ask_user_for_info(message: str):
            response = input(f"Agent: {message} \n Your response: \n)")
            return ActionResult(extracted_content=response)

class AgentController:
    def __init__(self):
        self.running = False
        self.loop = None
        self.agent_state = AgentState()
        
    def initialize_agent(self, task: str):
        initial_actions = [
            {'open_tab': {'url': 'https://www.google.com'}},
        ]
        self.agent = Agent(
            task=task,
            llm=ChatOpenAI(model='gpt-4o-mini'),
            initial_actions=initial_actions,
            injected_agent_state=self.agent_state,
            controller = CustomController(self)
        )

    async def run_agent(self):
        self.running = True
        self.loop = asyncio.get_event_loop()
        history = await self.agent.run()
        self.running = False

    def start(self):
        asyncio.run(self.run_agent())

    def pause(self):
        self.agent.pause()
        
    def resume(self):
        self.agent.resume()

    def stop(self):
        if self.agent:
            self.agent.stop()
        self.running = False

# agent_controller = AgentController()
# agent_thread = None
agent = None
def create_ui():
    # Set up the Gradio UI.
    with gr.Blocks(title="Agent Controller with Gradio UI") as demo:
        gr.Markdown("# Agent Controller with Gradio UI")
        
        with gr.Row():
            start_btn = gr.Button("Start Agent")
            # pause_btn = gr.Button("Pause Agent")
            # resume_btn = gr.Button("Resume Agent")
            stop_btn = gr.Button("Stop Agent")
        
        with gr.Row():
            task = gr.Textbox(label="Your Task", lines = 10, placeholder="Type your task here...")
        
        with gr.Row():
            user_input = gr.Textbox(label="User Response", interactive=False, lines=2)
            submit_btn = gr.Button("Submit Answer")

        log_output = gr.Textbox(label="Log", interactive=False, lines=10)
        
        
        @start_btn.click(inputs=task, outputs=log_output)
        def start_agent(task:str):
            global agent_controller, agent_thread
            if agent_controller.running:
                return "Agent is already running."
            else:
                agent_controller.initialize_agent(task)
                if agent_thread is None or not agent_thread:
                    agent_thread = threading.Thread(target=agent_controller.start)
                    agent_thread.start()
                    return "Agent started."
                
        # @pause_btn.click(outputs=log_output)
        # def pause_agent():
        #     global agent_controller
        #     agent_controller.pause()
        #     return "Agent paused."

        # def resume_agent():
        #     global agent_controller
        #     agent_controller.resume()
        #     return "Agent resumed."
        
        @stop_btn.click(outputs=log_output)
        def stop_agent():
            global agent_controller, agent_thread
            agent_controller.stop()
            if agent_thread:
                agent_thread.join()
            return "Agent stopped."
        
        @submit_btn.click(inputs=user_input, outputs=log_output)
        def submit_user_input(user_input:str):
            global user_response_future, agent_controller
            if user_response_future and not user_response_future.done():
                agent_controller.loop.call_soon_threadsafe(
                    user_response_future.set_result, user_input
                )
                return "Response submitted."
            return "No response needed."
        return demo

def main():
    demo = create_ui()
    demo.launch()
    
if __name__ == "__main__":
    main()
