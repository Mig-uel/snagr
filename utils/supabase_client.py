import os

from supabase import Client, create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

_supabase: Client = None


def get_supabase() -> Client:
    global _supabase

    if _supabase is None:
        _supabase = create_client(url, key)

    return _supabase
