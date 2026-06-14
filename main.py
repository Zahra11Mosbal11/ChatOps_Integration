import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Import network_utils.py 
from network_utils import isDeviceOnline, getAllStatues, findPath, deviceHealth, DEVICE_LIST

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# command handlers

# the /start command to send an introductory message to the user explaining how to use the bot.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    intro_message = (
        " **Welcome to the ChatOps Network Monitor!**\n\n"
        "I can help you monitor the status of network devices in real-time.\n\n"
        "**Available Commands:**\n"
        "`/start` - Show this welcome message.\n"
        "`/status` - View the UP/DOWN status of all predefined core devices.\n"
        "`/routes <IP>` - Trace the network path to a specific destination.\n"
        "`/check <IP>` - Perform an on-demand reachability check for an IP or hostname.\n\n"
        "*Example:* `/check 1.1.1.1`"
    )
    await update.message.reply_text(intro_message, parse_mode='Markdown')
    logger.info(f"User {update.effective_user.id} requested /start")


# the /check command to check the status of a specific device.
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    user_id = update.effective_user.id
    
    if not context.args:
        error_msg = "⚠️ Please provide an IP address or hostname to check.\n*Usage:* `/check <IP>`"
        await update.message.reply_text(error_msg, parse_mode='Markdown')
        logger.warning(f"User {user_id} issued /check with no IP.")
        return
    
    target_host_ip = context.args[0]
    
    status_msg = await update.message.reply_text(
        f" Checking status for `{target_host_ip}`...", 
        parse_mode='Markdown'
    )
    
    result = await isDeviceOnline(target_host_ip)
    await status_msg.edit_text(result, parse_mode='Markdown')


# the /status command to check the status of all predefined devices and sends the report.
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    user_id = update.effective_user.id
    logger.info(f"User {user_id} requested /status group check.")
    
    status_msg = await update.message.reply_text(
        "Checking the status of all predefined devices. Please wait...",
        parse_mode='Markdown'
    )
    
    report = await getAllStatues()
    await status_msg.edit_text(report, parse_mode='Markdown')

# the /routes command to trace the network path to a specific device.
async def routes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    user_id = update.effective_user.id
    
    if not context.args:
        error_msg = "⚠️ Please provide an IP address or hostname to trace.\n*Usage:* `/routes <IP>`"
        await update.message.reply_text(error_msg, parse_mode='Markdown')
        logger.warning(f"User {user_id} issued /routes with no IP.")
        return
        
    target_host_ip = context.args[0]
    
    status_msg = await update.message.reply_text(
        f" Tracing route to `{target_host_ip}`. This may take up to 20-30 seconds...", 
        parse_mode='Markdown'
    )
    
    result = await findPath(target_host_ip)
    
    await status_msg.edit_text(result, parse_mode='Markdown')

async def monitor_network_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Executing periodic network monitor job...")
    
    alert_chat_id = os.getenv("ALERT_CHAT_ID")
    if not alert_chat_id:
        logger.warning("Automated job skipped: ALERT_CHAT_ID is not configured in .env.")
        return
        
    for name, host_ip in DEVICE_LIST.items():
        alert_msg = await deviceHealth(name, host_ip)
        
        if alert_msg:
            await context.bot.send_message(
                chat_id=alert_chat_id, 
                text=alert_msg, 
                parse_mode='Markdown'
            )

# initialization

def main() -> None:
   
    load_dotenv()
    
    bot_token = os.getenv("TELEGRAM_TOKEN")
    if not bot_token:
        logger.error("Missing TELEGRAM_TOKEN. Please ensure it is set in the .env file.")
        return

    logger.info("Initializing Telegram bot application...")
    app = ApplicationBuilder().token(bot_token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("routes", routes))
    
    if app.job_queue:
        app.job_queue.run_repeating(monitor_network_job, interval=60, first=10)
    else:
        logger.error("Job Queue is not initialized! Make sure you are using python-telegram-bot[job-queue]")

    logger.info("Bot is polling for updates...")
    app.run_polling()

if __name__ == '__main__':
    main()
