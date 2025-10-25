# UPenn Token Gating & Monitoring — Quick Start 

## Step 1) Install dependencies

```bash
pip install flask requests pyarmor
```

## Step 2) Generate & distribute tokens

You already have `generate_tokens.py`. Run:

```bash
python generate_tokens.py
# Produces/updates active_tokens.json (JSON array)
```

Pick **one token** from `active_tokens.json` and send it to the collaborator (do **not** send the whole file).

## Step 3) Add “minimal check + log upload” at the top of the collaborator’s entry file

Place this **at the very beginning** of their entry script (before any business logic):

```python
# In the collaborator's entry file
import json
from main import upload_log  # reuse your upload function only

with open("active_tokens.json", "r", encoding="utf-8") as f:
    allow = set(json.load(f))

token = input("Enter token: ").strip()
if token not in allow:
    print("❌ Invalid token."); raise SystemExit(1)


upload_log(token)  

# Continue with their pipeline
run_their_pipeline()  # ← replace with the collaborator’s real entry call
```

> Tip: Ensure your `main.py` has the standard guard so importing `upload_log` does not auto-run your main:
>
> ```python
> if __name__ == "__main__":
>     main()
> ```

## Step 4) Encrypt and ship with PyArmor

```bash
# Encrypt a single file
pyarmor gen -O dist main.py

```

**Send to the collaborator**: the encrypted artifact + their token.

## Step 5) UPenn monitoring

1. **Backend (receives logs)**

```bash
python log_server.py
# Listening on http://127.0.0.1:8888
```

2. **Frontend (live viewer)**
   Open `http://127.0.0.1:8888/` in a browser and click “Connect” to see logs in real time.

## Step 6) Collaborator usage & outcomes

**Run**

```bash
python <their_entry>.py

```

**If validation succeeds**

* Their pipeline runs normally.
* Calls to `upload_log(...)` send lightweight markers (e.g., start/end/error) to your backend; the live viewer shows them immediately.

**If validation fails**

* The script exits (or prints “Invalid token”).
* **No** logs are sent (nothing appears in the viewer).

---
![Terminal run success](images/run-main-success.png)
![Realtime log viewer](images/frontend-viewer.png)
![Flask server receiving logs](images/server-console.png)
