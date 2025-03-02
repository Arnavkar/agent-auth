import asyncio
import threading
import gradio as gr

# Import your agent and controller libraries
from langchain_openai import ChatOpenAI
from browser_use import Agent
from browser_use.agent.views import ActionResult
from browser_use.controller.service import Controller

# Global variables to hold the agent's event loop and current user response future

# user_response_future = None

# Custom controller that registers a custom action using Gradio for user feedback.
# class CustomController(Controller):
#     def __init__(self, exclude_actions: list[str] = [], output_model: Optional[Type[BaseModel]] = None):
#         super().__init__(exclude_actions=exclude_actions, output_model=output_model)
#         self._register_custom_actions()

#     def _register_custom_actions(self):
#         @self.registry.action("Ask user for more information")
#         async def ask_user_for_info(message: str):
#             global user_response_future, agent_event_loop
#             # Create a new future on the agent's event loop.
#             user_response_future = agent_event_loop.create_future()
#             print("Agent is asking:", message)
#             # Wait until the future is resolved by the UI.
#             response = await user_response_future
#             print("Received answer from UI:", response)
#             return ActionResult(extracted_content=response)
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

controller = AgentController()
agent_thread = None
# Gradio callbacks for controlling the agent.
def start_agent(task:str):
    global controller, agent_thread
    if controller.running:
        return "Agent is already running."
    else:
        controller.initialize_agent(task)
        if agent_thread is None or not agent_thread:
            agent_thread = threading.Thread(target=controller.start)
            agent_thread.start()
            return "Agent started."

def pause_agent():
    global controller
    controller.pause()
    return "Agent paused."

def resume_agent():
    global controller
    controller.resume()
    return "Agent resumed."

def stop_agent():
    global controller, agent_thread
    controller.stop()
    if agent_thread:
        agent_thread.join()
        
    return "Agent stopped."

# # Callback for when the user submits an answer to the agent's question.
# def submit_user_input(answer: str) -> str:
#     global user_response_future, agent_event_loop
#     if user_response_future is not None and not user_response_future.done():
#         # Use a thread-safe call to set the result on the agent's event loop.
#         agent_event_loop.call_soon_threadsafe(user_response_future.set_result, answer)
#         # Reset the future so that subsequent calls do not affect the same one.
#         user_response_future = None
#         return f"Answer submitted: {answer}"
#     else:
#         return "No question pending."

def create_ui():
    # Set up the Gradio UI.
    with gr.Blocks(title="Agent Controller with Gradio UI") as demo:
        gr.Markdown("# Agent Controller with Gradio UI")
        
        with gr.Row():
            start_btn = gr.Button("Start Agent")
            pause_btn = gr.Button("Pause Agent")
            resume_btn = gr.Button("Resume Agent")
            stop_btn = gr.Button("Stop Agent")
        
        with gr.Row():
            task = gr.Textbox(label="Your Task", lines = 10, placeholder="Type your task here...")
        
        # with gr.Row():
        #     user_input = gr.Textbox(label="User Response", interactive=False, lines=2)
        #     submit_btn = gr.Button("Submit Answer")


        log_output = gr.Textbox(label="Log", interactive=False, lines=10)
        
        # Bind the button clicks to our callbacks.
        start_btn.click(start_agent, inputs=task, outputs=log_output)
        pause_btn.click(pause_agent, outputs=log_output)
        resume_btn.click(resume_agent, outputs=log_output)
        stop_btn.click(stop_agent, outputs=log_output)
        # submit_btn.click(submit_user_input, inputs=user_input, outputs=log_output)
    return demo

def main():
    demo = create_ui()
    demo.launch()
    
if __name__ == "__main__":
    main()
