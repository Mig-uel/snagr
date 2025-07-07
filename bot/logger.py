from datetime import datetime


def init_log():
    now = datetime.now()
    timestamp = now.strftime("%B %d, %Y @ %I:%M %p")

    print(f"[{timestamp}] TELEGRAM BOT STARTED RUNNING")


def logger(
    message,
    user,
    extra="",
):
    now = datetime.now()
    timestamp = now.strftime("%B %d, %Y @ %I:%M %p")

    # Logger
    if extra:
        print(
            f"[{timestamp}] | [COMMAND] {message.text} | [USER] {user.first_name} {user.last_name or ''} (@{user.username}) | [ID] {user.id} | [{extra}]"
        )
    else:
        print(
            f"[{timestamp}] | [COMMAND] {message.text} | [USER] {user.first_name} {user.last_name or ''} (@{user.username}) | [ID] {user.id}"
        )
