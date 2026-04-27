import json
import os
import sys
import time

import requests


def _rapid_host() -> str:
    return os.getenv("RAPIDAPI_HOST", "local-business-data.p.rapidapi.com")


def _debug_enabled() -> bool:
    return os.getenv("LOCAL_BUSINESS_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}


def _debug_log(message: str, **fields: object) -> None:
    if not _debug_enabled():
        return
    payload = {"message": message, **fields}
    print(f"[local-business-debug] {json.dumps(payload, ensure_ascii=True, default=str)}", file=sys.stderr, flush=True)


def fetch_local_business_data(query: str) -> str:
    """Fetch local business data from RapidAPI and return normalized JSON string."""
    rapidapi_key = "c39efb5a4emshfb8ff145889886cp172eebjsna4796494b900"
    rapidapi_host = "local-business-data.p.rapidapi.com"
    if not rapidapi_key:
        raise ValueError("Missing RAPIDAPI_KEY in environment variables.")

    url = f"https://{rapidapi_host}/search"

    querystring = {
        "query": query,
        "limit": "10",
        "zoom": "13",
        "language": "en",
        "extract_emails_and_contacts": "false",
    }

    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": rapidapi_host,
        "Content-Type": "application/json",
    }


    _debug_log(
        "search_request",
        query=query,
        limit=querystring["limit"],
        language=querystring["language"],
        host=rapidapi_host,
    )

    time.sleep(1)
    response = requests.get(url, headers=headers, params=querystring, timeout=30)
    response.raise_for_status()
    res = response.json()
    _debug_log(
        "search_response",
        status_code=response.status_code,
        top_level_keys=list(res.keys()) if isinstance(res, dict) else [],
    )

    local_business = res.get("data", [])
    data = {}
    for item in local_business:
        about_info = item.get("about") or {}
        business_id = item.get("business_id") or item.get("name")
        data[business_id] = {
            "name": item.get("name"),
            "address": item.get("full_address"),
            "rating": item.get("rating"),
            "review_count": item.get("review_count"),
            "working_hours": item.get("working_hours", {}),
            "reviews_per_rating": item.get("reviews_per_rating"),
            "type": item.get("type", ""),
            "subtypes": item.get("subtypes", []),
            "summary": about_info.get("summary", ""),
        }

    _debug_log(
        "search_normalized",
        result_count=len(data),
        sample_business_ids=list(data.keys())[:3],
    )

    return json.dumps(data)


def fetch_business_reviews_by_id(
    business_id: str,
    limit: int = 20,
    sort_by: str = "most_relevant",
    language: str = "en",
    max_chars_per_review: int = 400,
) -> str:
    rapidapi_key = "c39efb5a4emshfb8ff145889886cp172eebjsna4796494b900"
    rapidapi_host = "local-business-data.p.rapidapi.com"
    if not rapidapi_key:
        raise ValueError("Missing RAPIDAPI_KEY in environment variables.")

    url = f"https://{rapidapi_host}/business-reviews-v2"

    safe_limit = max(1, min(int(limit), 100))
    safe_max_chars = max(80, min(int(max_chars_per_review), 1200))

    querystring = {
        "business_id": business_id,
        "limit": 10,
        "sort_by": sort_by,
        "language": language,
    }

    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": rapidapi_host,
        "Content-Type": "application/json",
    }


    _debug_log(
        "reviews_request",
        business_id=business_id,
        requested_limit=limit,
        safe_limit=safe_limit,
        sort_by=sort_by,
        language=language,
        max_chars_per_review=safe_max_chars,
    )

    response = requests.get(url, headers=headers, params=querystring, timeout=30)
    response.raise_for_status()
    res = response.json()
    _debug_log(
        "reviews_response",
        status_code=response.status_code,
        top_level_keys=list(res.keys()) if isinstance(res, dict) else [],
    )

    raw_reviews = res.get("data", {}).get("reviews", [])
    reviews = []
    empty_text_count = 0
    for review in raw_reviews:
        text = (review.get("review_text") or "").strip()
        if not text:
            empty_text_count += 1
        reviews.append(
            {
                "rating": review.get("rating"),
                "review_time": review.get("review_time"),
                "review_text": text[:safe_max_chars],
            }
        )

    _debug_log(
        "reviews_normalized",
        business_id=business_id,
        raw_review_count=len(raw_reviews),
        returned_count=len(reviews),
        empty_text_count=empty_text_count,
        non_empty_text_count=len(reviews) - empty_text_count,
        first_review_text_length=len(reviews[0].get("review_text", "")) if reviews else 0,
    )

    payload = {
        "business_id": business_id,
        "requested_limit": safe_limit,
        "returned_count": len(reviews),
        "reviews": reviews,
    }

    return json.dumps(payload)
