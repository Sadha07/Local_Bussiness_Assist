import requests

url = "https://local-business-data.p.rapidapi.com/business-reviews-v2"

querystring = {"business_id":"0x3a525dafd2281aab:0x355f16a8a411dfdf"
               ,"limit":"30",
               "sort_by":"most_relevant"
               ,"language":"en"
               }

headers = {
	"x-rapidapi-key": "7749c738c4msh174d20804b83decp1ff0dejsn8f342d80faf0",
	"x-rapidapi-host": "local-business-data.p.rapidapi.com",
	"Content-Type": "application/json"
}

response = requests.get(url, headers=headers, params=querystring)
res = response.json()

local_bussines_reviews = res.get("data", {}).get("reviews", [])

bussiness_reviews = []
for review in local_bussines_reviews:
	bussiness_reviews.append({
		"rating": review.get("rating"),
		"review_time": review.get("review_time"),
		"review_text": review.get("review_text")
	})

print(bussiness_reviews)