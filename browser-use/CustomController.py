import pyperclip
from typing import Optional, Type
from pydantic import BaseModel
from browser_use.agent.views import ActionResult
from browser_use.browser.context import BrowserContext
from browser_use.controller.service import Controller
import logging

logger = logging.getLogger(__name__)

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