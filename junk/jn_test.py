import requests

url = "https://local-business-data.p.rapidapi.com/search"

querystring = {"query":"Hotels in San Francisco, USA","limit":"20","lat":"37.359428","lng":"-121.925337","zoom":"13","language":"en","region":"us","extract_emails_and_contacts":"false"}

headers = {
	"x-rapidapi-key": "d4eb285df8msheb9039973a4a4cap174586jsn9f40ae97d14b",
	"x-rapidapi-host": "local-business-data.p.rapidapi.com",
	"Content-Type": "application/json"
}

response = requests.get(url, headers=headers, params=querystring)
res = response.json()

local_bussiness = (res.get("data", []))
n = len(local_bussiness)
print("Total Bussiness found:", n)
data = {}
for i in range(n):
	data[local_bussiness[i].get("business_id")] = {
		"name": local_bussiness[i].get("name"),
		"address": local_bussiness[i].get("full_address"),
		"rating": local_bussiness[i].get("rating"),
		"review_count": local_bussiness[i].get("review_count"),
		"working_hours": local_bussiness[i].get("working_hours"),
		"reviews_per_rating" : local_bussiness[i].get("reviews_per_rating"),
		"type": local_bussiness[i].get("type"),
		"subtypes": local_bussiness[i].get("subtypes"),
        "summary": local_bussiness[i].get("about").get("summary")
	}
	
print(data)