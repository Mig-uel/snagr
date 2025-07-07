import subprocess
from pathlib import Path

import telebot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from logger import init_log, logger

parent_dir = Path(__file__).resolve().parent.parent

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

active = False


# /run
@bot.message_handler(commands=["run"])
def handle_run(message):
    global active

    # User
    user = message.from_user

    if user.id != int(TELEGRAM_CHAT_ID):
        logger(message=message, user=user, extra="UNAUTHORIZED")
        bot.send_message(message.chat.id, "<b>⛔ | Unauthorized</b>", parse_mode="HTML")
        return

    # TODO => SEARCH FOR ACTIVE PROCESS
    if active:
        logger(message=message, user=user, extra="ALREADY ACTIVE")
        bot.send_message(
            message.chat.id, "<b>⚠️ | Already running</b>", parse_mode="HTML"
        )
        return

    try:
        active = True

        logger(message=message, user=user, extra="TRIGGERED")

        subprocess.run([Path.joinpath(parent_dir, "run_scraper.sh")])

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
    finally:
        active = False


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


@bot.message_handler(commands=["status"])
def handle_status(message):
    global active

    user = message.from_user

    logger(message=message, user=user, extra=active)

    if active:
        bot.send_message(
            message.chat.id,
            "<b>ℹ️ | Status</b>\n\n<code>Running</code>",
            parse_mode="HTML",
        )
    else:
        bot.send_message(
            message.chat.id,
            "<b>ℹ️ | Status</b>\n\n<code>Idle</code>",
            parse_mode="HTML",
        )


if __name__ == "__main__":
    init_log()
    bot.polling()
