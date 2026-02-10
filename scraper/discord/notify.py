from os import getenv
from dotenv import load_dotenv
import requests

ENV_MODE = getenv("ENV_MODE", "development")
ENV_FILE = f".env.{ENV_MODE}"
load_dotenv(ENV_FILE, override=True)

DISCORD_WEBHOOK_URL = getenv('DISCORD_WEBHOOK_URL')

def build_message(message="", title="", href="", company="", time="", embed=None):
    if embed:
        return {
            "embeds": [{
                "title": title,
                "url": href,
                "description": message,
                "color": 0x00ff99,
                "footer": {
                    "text": company or time
                }
            }]
        }
    else:
        return {
            "content": message
        }

def send_message(json):
    requests.post(DISCORD_WEBHOOK_URL, json=json)
