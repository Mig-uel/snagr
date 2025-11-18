from os import getenv

from dotenv import load_dotenv

load_dotenv()
ENV_MODE = getenv("ENV_MODE", "development")
ENV_FILE = f".env.{ENV_MODE}"
load_dotenv(dotenv_path=ENV_FILE)

SUPABASE_URI = getenv("SUPABASE_URI")
SUPABASE_PASSWORD = getenv("SUPABASE_PASSWORD")
SUPABASE_URL = getenv("SUPABASE_URL")
SUPABASE_KEY = getenv("SUPABASE_KEY")

TELEGRAM_BOT_TOKEN = getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = getenv("TELEGRAM_CHAT_ID")

HEADLESS = getenv("HEADLESS", "True") == "True"
