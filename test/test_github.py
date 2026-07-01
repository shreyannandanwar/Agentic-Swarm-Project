import requests
import os
from dotenv import load_dotenv

load_dotenv()

headers = {
    "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"
}

url = "https://api.github.com/search/repositories"

params = {
    "q": "langgraph"
}

response = requests.get(
    url,
    headers=headers,
    params=params
)

print(response.json()["items"][0]["full_name"])