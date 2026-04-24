from langchain.tools import tool
import time
import requests
import json

@tool("get_bussiness")
def get_loca_bussiness_data(query: str) -> str:
    """
    Use this tool to search RapidAPI for local businesses, restaurants, and their reviews. You must provide a search query.
    Args:
        query (str): The query to search for local bussiness data.
    Returns:
        json: The list of local bussiness datas in json format.
    """
    print(query)
    url = "https://local-business-data.p.rapidapi.com/search"

    querystring = {"query":query,
                   "limit":"20",
                   "zoom":"13",
                   "language":"en",
                   "extract_emails_and_contacts":"false"}

    headers = {
    'x-rapidapi-key': "7749c738c4msh174d20804b83decp1ff0dejsn8f342d80faf0",
    'x-rapidapi-host': "local-business-data.p.rapidapi.com",
    'Content-Type': "application/json"
    }

    time.sleep(3) 

    response = requests.get(url, headers=headers, params=querystring)
    res = response.json()

    local_bussiness =  (res.get("data", []))

    n = len(local_bussiness)
    print("Total Bussiness found:", n)

    print(local_bussiness)
    data = {}
    for i in range(n):
        about_info = local_bussiness[i].get("about") or {}
        data[local_bussiness[i].get("business_id")] = {

		"name": local_bussiness[i].get("name"),
		"address": local_bussiness[i].get("full_address"),
		"rating": local_bussiness[i].get("rating"),
		"review_count": local_bussiness[i].get("review_count"),
		"working_hours": local_bussiness[i].get("working_hours",{}),
		"reviews_per_rating" : local_bussiness[i].get("reviews_per_rating"),
		"type": local_bussiness[i].get("type",""),
		"subtypes": local_bussiness[i].get("subtypes",[]),
        "summary": about_info.get("summary","")

	    }

    print(data)
    
    
        
    return json.dumps(data)
    
    