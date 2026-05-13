import requests

url = 'http://localhost:8000/api/extract/police-report'
files = {'file': open('sample_documents/Police_Report_Low_Complexity.pdf', 'rb')}
try:
    response = requests.post(url, files=files)
    print("STATUS:", response.status_code)
    print("JSON:", response.json())
except Exception as e:
    print("ERROR:", e)
