import subprocess
from pathlib import Path

import telebot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from is_scraper_running import is_scraper_running
from logger import init_log, logger

parent_dir = Path(__file__).resolve().parent.parent

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


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
            [str(parent_dir / "scripts/run_scraper.sh")],
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
        "<b>❓| Help</b>\n\n<code>/run - Run the scraper\n/status - Check status of the scraper</code>",
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


@bot.message_handler(commands=["start"])
def handle_start(message):
    user = message.from_user
    print(user)

    # args = message.text.split()

    # if len(args) > 1:
    #     payload = args[1]
    #     bot.send_message(message.chat.id, f"You came from: {payload}")
    # else:
    bot.send_message(
        message.chat.id,
        "<b>🤖 | Welcome</b>\n\nSnagr is a LinkedIn job scraper that runs every 30 minutes\n\nUse /help to get started",
        parse_mode="HTML",
    )


if __name__ == "__main__":
    init_log()
    bot.polling()
    bot.polling()
