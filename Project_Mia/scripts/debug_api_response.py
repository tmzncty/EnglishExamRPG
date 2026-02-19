import requests
import json
import sys

API_URL = "http://localhost:8000/api"
PAPER_ID = "2010-eng1"

def test_exam_api():
    print(f"Testing API: {API_URL}/exam/{PAPER_ID}")
    try:
        res = requests.get(f"{API_URL}/exam/{PAPER_ID}")
        if res.status_code != 200:
            print(f"Error: Status {res.status_code}")
            print(res.text)
            return

        data = res.json()
        print(f"Paper Title: {data.get('title')}")
        
        sections = data.get("sections", {})
        print("Sections found:", list(sections.keys()))
        
        # Check Reading A
        reading_a = sections.get("reading_a", [])
        print(f"Reading A Groups: {len(reading_a)}")
        
        if reading_a:
            first_group = reading_a[0]
            print(f"Group 1 Name: {first_group.get('group_name')}")
            print(f"Passage Length: {len(first_group.get('passage', ''))}")
            
            questions = first_group.get("questions", [])
            print(f"Questions in Group 1: {len(questions)}")
            
            if questions:
                q1 = questions[0]
                print("Question 1 Sample:")
                print(f"  ID: {q1.get('q_id')}")
                print(f"  Content: {q1.get('content')}")
                print(f"  Options Type: {type(q1.get('options'))}")
                print(f"  Options: {q1.get('options')}")
        
        # Check output
        with open("debug_response.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Saved full response to debug_response.json")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_exam_api()
