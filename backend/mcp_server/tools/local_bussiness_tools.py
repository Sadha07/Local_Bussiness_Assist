import json
import os
import time

import requests


def fetch_local_business_data(query: str) -> str:
    """Fetch local business data from RapidAPI and return normalized JSON string."""
    url = "https://api.openwebninja.com/local-business-data/search"
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    rapidapi_host = os.getenv("RAPIDAPI_HOST", "local-business-data.p.rapidapi.com")

    if not rapidapi_key:
        raise ValueError("Missing RAPIDAPI_KEY in environment variables.")

    querystring = {
        "query": query,
        "limit": "20",
        "zoom": "13",
        "language": "en",
        "extract_emails_and_contacts": "false",
    }

    headers = {
        "x-api-key": rapidapi_key,
        "Content-Type": "application/json",
    }

    time.sleep(1)
    response = requests.get(url, headers=headers, params=querystring, timeout=30)
    response.raise_for_status()
    res = response.json()

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

    return json.dumps(data)


def fetch_business_reviews_by_id(
    business_id: str,
    limit: int = 20,
    sort_by: str = "most_relevant",
    language: str = "en",
    max_chars_per_review: int = 400,
) -> str:
    url = "https://api.openwebninja.com/local-business-data/business-reviews"
    rapidapi_key = os.getenv("RAPIDAPI_KEY")

    if not rapidapi_key:
        raise ValueError("Missing RAPIDAPI_KEY in environment variables.")

    safe_limit = max(1, min(int(limit), 100))
    safe_max_chars = max(80, min(int(max_chars_per_review), 1200))

    querystring = {
        "business_id": business_id,
        "limit": str(safe_limit),
        "sort_by": sort_by,
        "language": language,
    }

    headers = {
        "x-api-key": rapidapi_key,
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers, params=querystring, timeout=30)
    response.raise_for_status()
    res = response.json()

    raw_reviews = res.get("data", {}).get("reviews", [])
    reviews = []
    for review in raw_reviews:
        text = (review.get("review_text") or "").strip()
        reviews.append(
            {
                "rating": review.get("rating"),
                "review_time": review.get("review_time"),
                "review_text": text[:safe_max_chars],
            }
        )

    payload = {
        "business_id": business_id,
        "requested_limit": safe_limit,
        "returned_count": len(reviews),
        "reviews": reviews,
    }

    return json.dumps(payload)
