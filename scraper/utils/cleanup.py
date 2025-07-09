import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from supabase import Client, create_client

from ..telegram import send_telegram_message

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

try:
    res = supabase.table("jobs").delete().lt("scraped_at", cutoff.isoformat()).execute()

    deleted = len(res.data)

    send_telegram_message(f"<b>🗑️ | Cleanup</b>\n\nDeleted {deleted} old job(s)")
except Exception as e:
    send_telegram_message(f"<b>⚠️ | Failed to clean up jobs</b>\n\n<code>{e}</code>")
