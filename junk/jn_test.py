import requests

url = "https://local-business-data.p.rapidapi.com/search"

querystring = {"query":"Hotels in San Francisco, USA","limit":"20","lat":"37.359428","lng":"-121.925337","zoom":"13","language":"en","region":"us","extract_emails_and_contacts":"false"}

headers = {
	"x-rapidapi-key": "c39efb5a4emshfb8ff145889886cp172eebjsna4796494b900",
	"x-rapidapi-host": "local-business-data.p.rapidapi.com",
	"Content-Type": "application/json"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())