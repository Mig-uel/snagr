from utils.supabase_client import get_supabase

supabase = get_supabase()


def get_existing_job_link() -> set[str]:
    return {
        item["job_link"]
        for item in supabase.table("jobs").select("job_link").execute().data
    }
