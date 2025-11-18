import os
from dotenv import load_dotenv
from supabase import Client, create_client

ENV_MODE = os.getenv("ENV_MODE", "development")
ENV_FILE = f".env.{ENV_MODE}"
load_dotenv(ENV_FILE, override=True)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

_supabase: Client = None


def get_supabase() -> Client:
    global _supabase

    if _supabase is None:
        _supabase = create_client(url, key)

    return _supabase
