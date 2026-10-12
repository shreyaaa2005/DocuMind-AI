import requests
import json

# 1. Login as demo-a
res_login = requests.post("http://127.0.0.1:8000/api/v1/auth/demo-login", json={"user_key": "demo-a"})
token = res_login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Upload PIXELCRAFT_Rubrics Round 2.pdf
with open(r"C:\Users\Acer\Downloads\PIXELCRAFT_Rubrics Round 2.pdf", "rb") as f:
    files = {"file": ("PIXELCRAFT_Rubrics Round 2.pdf", f, "application/pdf")}
    res_up = requests.post("http://127.0.0.1:8000/api/v1/documents/upload", files=files, headers=headers)
print("Upload status:", res_up.status_code, res_up.text[:200])

if res_up.status_code == 409:
    # Document already exists, retrieve its id
    docs = requests.get("http://127.0.0.1:8000/api/v1/documents/", headers=headers).json()
    doc_id = next(d["id"] for d in docs if "PIXELCRAFT" in d["original_filename"])
else:
    doc_id = res_up.json()["id"]

# 3. Process document
res_proc = requests.post(f"http://127.0.0.1:8000/api/v1/documents/{doc_id}/process", headers=headers)
print("Process status:", res_proc.status_code, res_proc.json())

# 4. Search with query 'what are the rubrics of pixel craft'
res_search = requests.post("http://127.0.0.1:8000/api/v1/search/", json={"query": "what are the rubrics of pixel craft"}, headers=headers)
print("\nSearch results count:", len(res_search.json()))
for r in res_search.json():
    sim = r["similarity_score"]
    doc_name = r["document_name"]
    text_prev = r["text"][:75]
    print(f"  Chunk sim={sim:.4f}, doc={doc_name}, text={text_prev}...")

# 5. QA Ask WITH document_id filter
res_qa_filtered = requests.post("http://127.0.0.1:8000/api/v1/qa/ask", json={
    "question": "what are the rubrics of pixel craft",
    "document_id": doc_id
}, headers=headers)
print("\n=== QA WITH DOCUMENT_ID FILTER ===")
print("Status:", res_qa_filtered.status_code)
print("Answer:", res_qa_filtered.json().get("answer"))
print("Citations count:", len(res_qa_filtered.json().get("citations", [])))
for cit in res_qa_filtered.json().get("citations", []):
    print(f"  Citation doc={cit['document_name']}, page={cit['page_start']}, sim={cit['similarity_score']:.4f}")

# 6. QA Ask WITHOUT document_id filter
res_qa_unfiltered = requests.post("http://127.0.0.1:8000/api/v1/qa/ask", json={
    "question": "what are the rubrics of pixel craft"
}, headers=headers)
print("\n=== QA WITHOUT DOCUMENT_ID FILTER ===")
print("Status:", res_qa_unfiltered.status_code)
print("Answer:", res_qa_unfiltered.json().get("answer"))
print("Citations count:", len(res_qa_unfiltered.json().get("citations", [])))
for cit in res_qa_unfiltered.json().get("citations", []):
    print(f"  Citation doc={cit['document_name']}, page={cit['page_start']}, sim={cit['similarity_score']:.4f}")
