import requests

res_login = requests.post("http://127.0.0.1:8000/api/v1/auth/demo-login", json={"user_key": "demo-a"})
token = res_login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

doc_id = "0705784f-84bc-487f-9bee-f77764fee630"

# Question 1
q1 = "Summarize the key architectural decisions and requirements"
r1 = requests.post("http://127.0.0.1:8000/api/v1/qa/ask", json={"question": q1, "document_id": doc_id}, headers=headers)
print("=== Question 1 (Default settings) ===")
print("Status:", r1.status_code)
print("Answer:\n", r1.json().get("answer"))
print("\nCitations count:", len(r1.json().get("citations", [])))
for c in r1.json().get("citations", []):
    print(f"  Citation: page={c['page_start']}, sim={c['similarity_score']:.4f}, doc={c['document_name']}")

# Question 2
q2 = "what is this research paper includes"
r2 = requests.post("http://127.0.0.1:8000/api/v1/qa/ask", json={"question": q2, "document_id": doc_id}, headers=headers)
print("\n=== Question 2 (Default settings) ===")
print("Status:", r2.status_code)
print("Answer:\n", r2.json().get("answer"))
print("\nCitations count:", len(r2.json().get("citations", [])))
for c in r2.json().get("citations", []):
    print(f"  Citation: page={c['page_start']}, sim={c['similarity_score']:.4f}, doc={c['document_name']}")
