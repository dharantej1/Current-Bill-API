from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import re

app = FastAPI(title="TG Southern Power Ultimate Bill API")

class BillInfoRequest(BaseModel):
    ukscno: str
    radio_option: str = "LT" 

@app.post("/api/billing-info")
def fetch_detailed_bill_info(request_data: BillInfoRequest):
    paybill_url = "https://tgsouthernpower.org/paybillonline"
    billing_info_url = "https://tgsouthernpower.org/billinginfo"
    
    session = requests.Session()
    
    try:
        # Establish session to grab cookies/JSESSIONID
        session.get("https://tgsouthernpower.org/onlinebillenquiry", timeout=10)

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://tgsouthernpower.org",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        # ==========================================
        # STEP 1: Extract EVERYTHING from /paybillonline
        # ==========================================
        paybill_payload = {"ukscno": request_data.ukscno}
        
        paybill_response = session.post(paybill_url, data=paybill_payload, headers=headers, allow_redirects=False, timeout=10)
        paybill_response.raise_for_status()
        
        paybill_soup = BeautifulSoup(paybill_response.text, "lxml")
        payment_summary = {}
        
        # Find all tables with the class 'ctable' (this catches both Consumer Details and Payment Details)
        for table in paybill_soup.find_all("table", class_="ctable"):
            for row in table.find_all("tr"):
                th = row.find("th")
                td = row.find("td")
                
                if th and td:
                    # Clean up the key: lowercase, replace spaces/slashes with underscores
                    raw_key = th.text.strip().lower()
                    key = re.sub(r'[^a-z0-9]', '_', raw_key) 
                    key = re.sub(r'_+', '_', key).strip('_') # Remove duplicate underscores
                    
                    # Clean up the value: remove extra spaces, newlines, and hidden inputs
                    if td.find("input"):
                        td.find("input").decompose() # Remove hidden inputs so they don't bloat the text
                        
                    value = td.text.strip()
                    value = re.sub(r'\s+', ' ', value) # Normalize spaces
                    
                    # Split dates if it's the combined date field (e.g., "02-Apr-26 / 16-Apr-26")
                    if "bill_date_due_date" in key and "/" in value:
                        dates = value.split("/")
                        payment_summary["bill_date"] = dates[0].strip()
                        payment_summary["due_date"] = dates[1].strip()
                    else:
                        payment_summary[key] = value

        # ==========================================
        # STEP 2: Extract EVERYTHING from /billinginfo
        # ==========================================
        billing_payload = {
            "inlineRadioOptions": request_data.radio_option,
            "ukscno": request_data.ukscno
        }
        
        headers["Referer"] = "https://tgsouthernpower.org/onlinebillenquiry"

        billing_response = session.post(billing_info_url, data=billing_payload, headers=headers, allow_redirects=False, timeout=10)
        billing_response.raise_for_status()
        
        billing_soup = BeautifulSoup(billing_response.text, "lxml")
        detailed_ledger = {
            "consumer_details": {},
            "arrears": {},
            "current_month_bill": {},
            "total_payable": {},
            "total_paid": {}
        }
        
        table = billing_soup.find("table", class_="table-bordered")
        if not table:
            raise HTTPException(status_code=404, detail="Billing table not found in the detailed response.")

        current_section = "consumer_details"

        for row in table.find_all("tr"):
            section_header = row.find("td", colspan="4")
            if section_header:
                section_text = section_header.text.strip().lower()
                if "arrears" in section_text:
                    current_section = "arrears"
                elif "current month" in section_text:
                    current_section = "current_month_bill"
                elif "payable" in section_text:
                    current_section = "total_payable"
                elif "paid :" in section_text:
                    current_section = "total_paid"
                continue

            ths = row.find_all("th")
            tds = row.find_all("td")
            
            for th, td in zip(ths, tds):
                raw_key = th.text.strip().lower()
                key = re.sub(r'[^a-z0-9]', '_', raw_key)
                key = re.sub(r'_+', '_', key).strip('_')
                
                value = td.text.strip()
                value = re.sub(r'\s+', ' ', value)
                
                detailed_ledger[current_section][key] = value

        # ==========================================
        # STEP 3: Return the Unified Payload
        # ==========================================
        return {
            "status": "success",
            "data": {
                "payment_summary": payment_summary,
                "detailed_ledger": detailed_ledger
            }
        }

    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed: {e}")
        raise HTTPException(status_code=502, detail="Failed to communicate with the utility server")