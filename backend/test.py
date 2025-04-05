import requests

url = "http://localhost:5000/get-prices"
payload = {"query": "second hand long satin red dress for wedding guest, medium women size, long and no arms"}
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
