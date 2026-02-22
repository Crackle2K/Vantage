"""Quick raw test of the API key — no project imports needed."""
import os, json, urllib.request
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("GOOGLE_API_KEY", "")
print(f"Key starts with: {key[:12]}")

url = (
    f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    f"?location=43.6532,-79.3832&radius=5000&key={key}"
)

resp = urllib.request.urlopen(url)
data = json.loads(resp.read())

status = data.get("status")
error = data.get("error_message", "none")
count = len(data.get("results", []))

print(f"Status : {status}")
print(f"Error  : {error}")
print(f"Results: {count}")

if count > 0:
    for r in data["results"][:3]:
        print(f"  - {r['name']}")
