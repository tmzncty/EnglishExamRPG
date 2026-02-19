import concurrent.futures
import requests
import time
import sys

def send_request(q_id):
    url = "http://localhost:8000/api/exam/submit_subjective"
    # Mock data
    data = {
        "q_id": q_id,
        "answer": f"Concurrent test answer for {q_id}. This is a stress test.",
        "section_type": "translation"
    }
    try:
        start_time = time.time()
        response = requests.post(url, json=data)
        end_time = time.time()
        duration = end_time - start_time
        print(f"[{q_id}] Status: {response.status_code}, Time: {duration:.2f}s")
        if response.status_code != 200:
            print(f"[{q_id}] Error Response: {response.text}")
        return response.status_code
    except Exception as e:
        print(f"[{q_id}] Request failed: {e}")
        return 500

def stress_test():
    q_ids = ["stress-trans-01", "stress-trans-02", "stress-trans-03"]
    print("🚀 Starting Concurrent Stress Test (3 requests)...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(send_request, q_id): q_id for q_id in q_ids}
        
        results = []
        for future in concurrent.futures.as_completed(futures):
            q_id = futures[future]
            try:
                status = future.result()
                results.append((q_id, status))
            except Exception as e:
                print(f"[{q_id}] Exception: {e}")
                results.append((q_id, 500))

    print("\n📊 Test Results:")
    all_passed = True
    for q_id, status in results:
        print(f" - {q_id}: {status}")
        if status != 200:
            all_passed = False
            
    if all_passed:
        print("\n✅ All requests passed successfully! No 500 errors.")
    else:
        print("\n❌ Some requests failed.")
        sys.exit(1)

if __name__ == "__main__":
    stress_test()
