from .supabase import get_supabase

supabase = get_supabase()


def get_existing_job_links() -> set[str]:
    all_links = set()
    page_size = 1000
    offset = 0

    while True:
        res = (
            supabase.table("jobs")
            .select("job_link")
            .range(offset, offset + page_size - 1)
            .execute()
        )

        data = res.data or []
        all_links.update(item["job_link"] for item in data)

        if len(data) < page_size:
            break  # no more rows

        offset += page_size

    return all_links
