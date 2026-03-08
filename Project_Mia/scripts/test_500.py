"""
Verify both /api/vocab/today and /api/vocab/global_stats endpoints.
"""
import urllib.request
from urllib.error import HTTPError
import json

endpoints = [
    "http://localhost:8000/api/vocab/today?slot_id=0",
    "http://localhost:8000/api/vocab/global_stats?slot_id=0",
]

for url in endpoints:
    print(f"\n🔍 Testing: {url}")
    try:
        resp = urllib.request.urlopen(url)
        data = json.loads(resp.read().decode())
        print(f"✅ Status: {resp.status}")
        # Print a summary, not full response
        if "tasks" in data:
            print(f"  tasks: {len(data['tasks'])} items, total_count: {data.get('total_count')}")
        else:
            print(f"  Response: {json.dumps(data)}")
    except HTTPError as e:
        body = e.read().decode()
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        print(f"  Body: {body[:500]}")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n🎉 All endpoint checks done!")
