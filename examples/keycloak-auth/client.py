import requests
import json

url = "http://localhost:8080/realms/dataclay/protocol/openid-connect/token"

payload = 'grant_type=password&client_id=direct-access-demo&scope=email%20openid&username=user&password=123'
headers = {
  'Content-Type': 'application/x-www-form-urlencoded'
}

response_data = json.loads(requests.request("POST", url, headers=headers, data=payload).text)
response = requests.request("POST", url, headers=headers, data=payload)

access_token = response_data.get("access_token")
print(access_token)
