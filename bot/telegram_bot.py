import os
import subprocess
from pathlib import Path

import telebot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from logger import init_log, logger

parent_dir = Path(__file__).resolve().parent.parent

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


# check if an instance of a scraper is already active
def is_scraper_running():
    if os.path.exists("/tmp/scraper.pid"):
        try:
            with open("/tmp/scraper.pid", "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # Check if process exists
        except (ValueError, ProcessLookupError):
            return False  # PID file is stale
        return True
    return False


# /run
@bot.message_handler(commands=["run"])
def handle_run(message):
    # User
    user = message.from_user

    if is_scraper_running():
        logger(message=message, user=user, extra="ALREADY ACTIVE")
        bot.send_message(
            message.chat.id, "<b>⚠️ | Scraper is already active</b>", parse_mode="HTML"
        )
        return

    if user.id != int(TELEGRAM_CHAT_ID):
        logger(message=message, user=user, extra="UNAUTHORIZED")
        bot.send_message(message.chat.id, "<b>⛔ | Unauthorized</b>", parse_mode="HTML")
        return

    try:
        logger(message=message, user=user, extra="TRIGGERED")

        subprocess.run(
            [str(parent_dir / "run_scraper.sh")],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=900,
        )

        logger(message=message, user=user, extra="FINISHED")
    except subprocess.TimeoutExpired:
        logger(message=message, user=user, extra="TIMEOUT ERROR")

        bot.send_message(
            message.chat.id,
            "<b>⚠️ | Scraper took too long</b>",
            parse_mode="HTML",
        )

    except Exception as e:
        logger(message=message, user=user, extra=e)

        bot.send_message(
            message.chat.id,
            f"<b>⚠️ | Error</b>\n\n<code>{e}</code>",
            parse_mode="HTML",
        )


# /help
@bot.message_handler(commands=["help"])
def handle_help(message):
    # User
    user = message.from_user

    logger(message=message, user=user)

    bot.send_message(
        message.chat.id,
        "<b>❓| Help</b>\n\n<code>/run - Run the scraper</code>",
        parse_mode="HTML",
    )


# /status
@bot.message_handler(commands=["status"])
def handle_status(message):
    user = message.from_user

    logger(message=message, user=user, extra=is_scraper_running())

    if is_scraper_running():
        bot.send_message(
            message.chat.id,
            "<b>🟢 | Status</b>\n\n<code>Active</code>",
            parse_mode="HTML",
        )
    else:
        bot.send_message(
            message.chat.id,
            "<b>⚪ | Status</b>\n\n<code>Idle</code>",
            parse_mode="HTML",
        )


if __name__ == "__main__":
    init_log()
    bot.polling()
