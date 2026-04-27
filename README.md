# TG Southern Power (Unofficial) API ⚡

An unofficial, lightweight REST API built with **FastAPI** that fetches and parses electricity bill details from the TG Southern Power (Telangana) website. 

This API acts as a proxy/scraper, taking in simple JSON requests, simulating browser sessions to bypass temporary cookie restrictions (`JSESSIONID`), and parsing complex HTML tables into clean, structured JSON data.

🌍 **Live Base URL:** `https://current-bill-api.vercel.app`
📖 **Interactive Docs (Swagger UI):** `https://current-bill-api.vercel.app/docs`

---

## 🚀 Features
* **Automated Session Handling:** Automatically fetches and manages `JSESSIONID` cookies so requests don't expire.
* **HTML Parsing:** Converts raw HTML table data from the utility portal into clean, nested JSON.
* **Dual Endpoints:** Supports both quick bill summaries and detailed chronological breakdowns (arrears, paid dates, etc.).
* **Fast & Validated:** Built on FastAPI with Pydantic for automatic request validation.

---

## 🛠️ Tech Stack
* **Python 3.9+**
* **FastAPI** (Web framework)
* **Requests** (HTTP & Session management)
* **BeautifulSoup4 / lxml** (HTML parsing & scraping)
* **Uvicorn** (ASGI server)

---

## 📡 API Endpoints

### 1. Basic Bill Summary
Fetches the standard billing overview, including the current month's bill and due date.

* **Endpoint:** `POST /api/fetch-bill`
* **Content-Type:** `application/json`

**Request Body:**
```json
{
  "ukscno": "XXXXXXXXX"
}
```

**Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "consumer_name": "[REDACTED NAME]",
    "ukscno": "XXXXXXXXX",
    "service_number": "XXXX XXXXX",
    "address": "[REDACTED ADDRESS]",
    "units_consumed": "217",
    "bill_date": "02-Apr-26",
    "due_date": "16-Apr-26",
    "current_month_bill": 1321.0,
    "total_amount_due": 0.0
  }
}
```

### 2. Detailed Billing Info
Fetches a granular breakdown of the bill, grouped by arrears, current charges, total payable, and last paid amounts.

* **Endpoint:** `POST /api/billing-info`
* **Content-Type:** `application/json`

**Request Body:**
```json
{
  "ukscno": "XXXXXXXXX",
  "radio_option": "LT" 
}
```
*(Note: `radio_option` defaults to "LT" if omitted).*

**Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "consumer_details": {
      "consumer_name": "[REDACTED NAME]",
      "unique_service_number": "XXXXXXXXX",
      "service_number": "XXXX XXXXX",
      "ero": "[REDACTED ERO]",
      "address": "[REDACTED ADDRESS]",
      "section_name": "[REDACTED SECTION]"
    },
    "arrears": {
      "date": "31-MAR-26",
      "amount": "0"
    },
    "current_month_bill": {
      "date": "02-APR-26",
      "amount": "1321"
    },
    "total_payable": {
      "due_date": "16-APR-26",
      "amount": "1321"
    },
    "total_paid": {
      "paid_date": "07-APR-26",
      "paid_amount": "1321.0"
    }
  }
}
```

---

## 💻 Local Setup & Development

If you want to run this API on your own machine:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dharantej1/Current-Bill-API.git
   cd Current-Bill-API
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server:**
   ```bash
   uvicorn main:app --reload
   ```
   The API will now be running at `http://127.0.0.1:8000`. Navigate to `http://127.0.0.1:8000/docs` to test it.

---

## ⚠️ Disclaimer & IP Blocking Notice

This is an **unofficial API** and is not affiliated with, endorsed by, or connected to TG Southern Power Distribution Company of Telangana Limited. 

**Important note on Hosting:** Because this API functions as a web scraper, utility firewalls (like AWS WAF or Cloudflare) may occasionally block incoming requests originating from data center IP addresses (like AWS, Vercel, or Render). If the API begins returning `502 Bad Gateway` or `Timeout` errors while hosted in the cloud, you may need to route the Python `requests` session through a Residential Proxy network. Use responsibly and avoid sending high-frequency bulk requests.