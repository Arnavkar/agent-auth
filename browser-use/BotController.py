from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from AgentController import AgentController
from enum import Enum
from models import *
import os
import asyncio
import logging
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class BotController():
    def __init__(self):
        self.agent_controller = AgentController()
        self.State = BotStates
        self._get_token()
        self.future = None
        self.task = None
        
    def _get_token(self):
        self.TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
        if not self.TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN environment variable not found.")
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text(
            "🚀 Welcome to LetMeDoThatForYou Bot!\n"
            "What would you like me to do for you today?\n"
        )
        return self.State.PROMPT_RECEIVED

    async def launch_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_prompt = update.message.text.lower()
        await update.message.reply_text("🔄 Spinning up your session...")
        
        async def send_agent_message(agent_message):
            await context.bot.send_message(update.message.chat_id, agent_message)
            self.future = asyncio.get_event_loop().create_future()
            response = await self.future
            return response

        self.agent_controller.register_ask_user(send_agent_message)
        await self.agent_controller.initialize_agent(user_prompt)
        self.task = asyncio.create_task(self.agent_controller.run_task())
        return self.State.PROCESSING
        
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("❌ Process cancelled.")
        self.agent_controller.cancel_run()
        return ConversationHandler.END
    
    async def handle_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_response = update.message.text
        await update.message.reply_text("🔄 Processing...")
        self.future.set_result(user_response)
        
    async def complete_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("🎉 Task complete! 🎉")
        await update.message.reply_text(self.task.result())
                       
    def main(self) -> None:
        application = Application.builder().token(os.environ["TELEGRAM_TOKEN"]).build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                BotStates.PROMPT_RECEIVED: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.launch_session),
                ],
                BotStates.PROCESSING: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_response),
                ],
                BotStates.TASK_COMPLETE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.complete_task),
                ]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )

        application.add_handler(conv_handler)
        application.run_polling()

if __name__ == "__main__":
    load_dotenv()
    bot = BotController()
    bot.main()



