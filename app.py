from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from datetime import datetime

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== CONFIG ==================
AIRTABLE_API_KEY = "YOUR_AIRTABLE_API_KEY"
AIRTABLE_BASE_ID = "YOUR_BASE_ID"
AIRTABLE_TABLE = "YOUR_TABLE"

# ================== MODEL ==================
class ClientData(BaseModel):
    brand_name: str
    account_manager: str
    category: str
    start_date: str
    deliverables: int
    billing_email: str
    invoice_cycle: str

# ================== AGENT ==================
def validate_client(data):
    issues = []

    if not data.billing_email:
        issues.append("Missing email")

    if data.deliverables <= 0:
        issues.append("Invalid deliverables")

    return {
        "status": "proceed" if not issues else "hold",
        "issues": issues
    }

# ================== EMAIL ==================
def send_email(data):
    print(f"📧 Email sent to {data.billing_email}")
    return True

# ================== DRIVE ==================
def create_drive_folder(data):
    return f"https://drive.fake/{data.brand_name}_{data.start_date}"

# ================== NOTION ==================
def create_notion_page(data):
    return f"https://notion.fake/{data.brand_name}"

# ================== AIRTABLE ==================
def create_airtable_record(data, drive_link, notion_link):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}"

    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "fields": {
            "Brand Name": data.brand_name,
            "Account Manager": data.account_manager,
            "Start Date": data.start_date,
            "Deliverables": data.deliverables,
            "Billing Email": data.billing_email,
            "Drive Link": drive_link,
            "Notion Link": notion_link
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# ================== LOG ==================
def log(status, msg):
    print(f"[{datetime.now()}] {status}: {msg}")

# ================== FRONTEND ==================
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Client Onboarding</title>
        <style>
            body { font-family: Arial; background:#f4f6f8; display:flex; justify-content:center; padding-top:40px; }
            .box { background:white; padding:20px; border-radius:10px; width:400px; box-shadow:0 5px 15px rgba(0,0,0,0.1);}
            input, select { width:100%; padding:10px; margin:8px 0; }
            button { width:100%; padding:12px; background:#007bff; color:white; border:none; }
            #result { margin-top:10px; }
        </style>
    </head>
    <body>
    <div class="box">
        <h2>Client Onboarding</h2>
        <form id="form">
            <input placeholder="Brand Name" id="brand_name" required>
            <input placeholder="Account Manager" id="account_manager" required>
            <input placeholder="Category" id="category" required>
            <input type="date" id="start_date" required>
            <input type="number" placeholder="Deliverables" id="deliverables" required>
            <input type="email" placeholder="Billing Email" id="billing_email" required>
            <select id="invoice_cycle">
                <option value="Monthly">Monthly</option>
                <option value="Quarterly">Quarterly</option>
            </select>
            <button type="submit">Start</button>
        </form>
        <div id="result"></div>
    </div>

    <script>
    document.getElementById("form").addEventListener("submit", async function(e){
        e.preventDefault();

        const data = {
            brand_name: document.getElementById("brand_name").value,
            account_manager: document.getElementById("account_manager").value,
            category: document.getElementById("category").value,
            start_date: document.getElementById("start_date").value,
            deliverables: parseInt(document.getElementById("deliverables").value),
            billing_email: document.getElementById("billing_email").value,
            invoice_cycle: document.getElementById("invoice_cycle").value
        };

        const res = await fetch("/onboard", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        });

        const result = await res.json();

        document.getElementById("result").innerHTML =
            result.status === "success"
            ? "✅ Success<br>Drive: " + result.drive
            : "❌ Error: " + result.issues;
    });
    </script>
    </body>
    </html>
    """

# ================== MAIN API ==================
@app.post("/onboard")
def onboard(client: ClientData):

    log("START", client.brand_name)

    validation = validate_client(client)

    if validation["status"] == "hold":
        return {"status": "error", "issues": validation["issues"]}

    send_email(client)
    drive = create_drive_folder(client)
    notion = create_notion_page(client)
    airtable = create_airtable_record(client, drive, notion)

    log("SUCCESS", client.brand_name)

    return {
        "status": "success",
        "drive": drive,
        "notion": notion,
        "airtable": airtable
    }