import requests
import json

def test_compile():
    print("Welcome to Vibe CAD Designer!")
    user_prompt = input("Enter your design prompt (e.g. 'Create a cylinder...'): ")
    
    if not user_prompt.strip():
        print("Empty prompt. Exiting.")
        return

    url = "http://127.0.0.1:8000/compile"
    payload = {
        "prompt": user_prompt
    }
    
    print(f"\nSending request to {url}...")
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        print("\n--- Success! Received D-File ---")
        print(json.dumps(data, indent=2))
        
        # Optional: Save to file for execution
        with open("output_test.json", "w") as f:
            json.dump(data, f, indent=2)
            print("\nSaved to output_test.json")

        # --- EXECUTION STEP ---
        if "error" not in data:
            do_exec = input("\nDo you want to EXECUTE this in CATIA V5? (y/n): ")
            if do_exec.lower() == 'y':
                exec_url = "http://127.0.0.1:8000/execute"
                exec_payload = {
                    "mode": "real",
                    "d_file": data
                }
                print(f"Sending to CATIA ({exec_url})...")
                exec_response = requests.post(exec_url, json=exec_payload)
                print("Execution Result:", exec_response.json())
        else:
             print("Skipping execution due to compilation error.")

    except Exception as e:
        print(f"Error: {e}")
        try:
           print("Server response:", response.text)
        except:
           pass

if __name__ == "__main__":
    test_compile()
