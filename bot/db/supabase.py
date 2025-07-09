import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

_supabase: Client = None


def get_supabase() -> Client:
    global _supabase

    if _supabase is None:
        _supabase = create_client(url, key)

    return _supabase
