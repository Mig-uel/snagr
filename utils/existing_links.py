from utils.supabase_client import get_supabase

supabase = get_supabase()


def get_existing_job_link() -> set[str]:
    res = supabase.table("jobs").select("job_link").limit(None).execute()
    return {item["job_link"] for item in res.data}
