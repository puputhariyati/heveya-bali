import requests

url = "https://stoplight.io/mocks/jurnal-mekari/jurnal-api/182542/api/v1/customers"

headers = {
    "Accept": "application/json",
    "Prefer": "code=200, dynamic=true",
    "apikey": "123"
}

response = requests.get(url, headers=headers)
print(response.json())

