import requests, time, random

while True:
    payload = {
        "temperature": round(random.uniform(75, 80), 2)
    }
    r = requests.post("http://localhost:3001/update/temp",
                      json=payload)
    print(r.status_code)
    time.sleep(5)




