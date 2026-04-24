"""
main.py
The main entry point for the ChatOps Network Monitor bot.
Initializes the Telegram bot and registers command handlers.
"""
import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Import our modular network utilities
from network_utils import check_device_status, check_all_devices_status, trace_route

# Configure logging to help with debugging and monitoring
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /start command.
    Sends an introductory message to the user explaining how to use the bot.
    """
    intro_message = (
        "🤖 **Welcome to the ChatOps Network Monitor!**\n\n"
        "I can help you monitor the status of network devices in real-time.\n\n"
        "**Available Commands:**\n"
        "`/start` - Show this welcome message.\n"
        "`/status` - View the UP/DOWN status of all predefined core devices.\n"
        "`/routes <IP>` - Trace the network path to a specific destination.\n"
        "`/check <IP>` - Perform an on-demand reachability check for an IP or hostname.\n\n"
        "*Example:* `/check 1.1.1.1`"
    )
    # Send message with Markdown formatting
    await update.message.reply_text(intro_message, parse_mode='Markdown')
    logger.info(f"User {update.effective_user.id} requested /start")


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /check command.
    Extracts the IP from the user's message, validates it, and returns the status.
    """
    user_id = update.effective_user.id
    
    # context.args contains the arguments passed after the command
    if not context.args:
        error_msg = "⚠️ Please provide an IP address or hostname to check.\n*Usage:* `/check <IP>`"
        await update.message.reply_text(error_msg, parse_mode='Markdown')
        logger.warning(f"User {user_id} issued /check with no IP.")
        return
    
    # Extract the first argument as target IP
    target_ip = context.args[0]
    
    # Inform the user that the request is being processed
    status_msg = await update.message.reply_text(
        f"⏳ Checking status for `{target_ip}`...", 
        parse_mode='Markdown'
    )
    
    # Call the async ping utility function
    # Because check_device_status is asynchronous, it won't block other bot interactions
    result = await check_device_status(target_ip)
    
    # Update the status message with the final result
    await status_msg.edit_text(result, parse_mode='Markdown')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /status command.
    Retrieves the status for all predefined devices and sends the report.
    """
    user_id = update.effective_user.id
    logger.info(f"User {user_id} requested /status group check.")
    
    # Inform the user
    status_msg = await update.message.reply_text(
        "⏳ Checking the status of all predefined devices. Please wait...",
        parse_mode='Markdown'
    )
    
    # Fetch result
    report = await check_all_devices_status()
    
    # Send report
    await status_msg.edit_text(report, parse_mode='Markdown')

async def routes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /routes command.
    Performs a traceroute to the specified IP.
    """
    user_id = update.effective_user.id
    
    if not context.args:
        error_msg = "⚠️ Please provide an IP address or hostname to trace.\n*Usage:* `/routes <IP>`"
        await update.message.reply_text(error_msg, parse_mode='Markdown')
        logger.warning(f"User {user_id} issued /routes with no IP.")
        return
        
    target_ip = context.args[0]
    
    status_msg = await update.message.reply_text(
        f"⏳ Tracing route to `{target_ip}`. This may take up to 20-30 seconds...", 
        parse_mode='Markdown'
    )
    
    result = await trace_route(target_ip)
    
    await status_msg.edit_text(result, parse_mode='Markdown')

# --- INITIALIZATION ---

def main() -> None:
    """
    Main function to initialize and run the Telegram bot.
    Implementing DevSecOps best practices by loading secrets securely via python-dotenv.
    """
    # 1. Load environment variables securely from .env file
    load_dotenv()
    
    bot_token = os.getenv("TELEGRAM_TOKEN")
    if not bot_token:
        # Fail gracefully if token is missing
        logger.error("Missing TELEGRAM_TOKEN. Please ensure it is set in the .env file.")
        return

    logger.info("Initializing Telegram bot application...")
    # 2. Build the application using the python-telegram-bot ApplicationBuilder
    app = ApplicationBuilder().token(bot_token).build()

    # 3. Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("routes", routes))

    # 4. Start polling for updates from Telegram
    logger.info("Bot is polling for updates...")
    app.run_polling()

if __name__ == '__main__':
    main()
