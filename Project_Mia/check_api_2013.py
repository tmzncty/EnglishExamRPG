import urllib.request
import json

url = "http://localhost:8000/api/exam/2013-eng1"
try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read())
        wb = data.get("sections", {}).get("writing_b", {})
        img = wb.get("image")
        print(f"Structure keys: {list(wb.keys())}")
        print(f"Image type: {type(img)}")
        if img:
            print(f"Image len: {len(img)}")
            print(f"Image start: {img[:50]}")
        else:
            print("Image is None/Empty")
except Exception as e:
    print(e)
