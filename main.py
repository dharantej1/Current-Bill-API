from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import re

app = FastAPI(title="TG Southern Power Detailed Bill API")

class BillInfoRequest(BaseModel):
    ukscno: str
    radio_option: str = "LT" # Defaulting to LT as seen in your payload

@app.post("/api/billing-info")
def fetch_detailed_bill_info(request_data: BillInfoRequest):
    target_url = "https://tgsouthernpower.org/billinginfo"
    session = requests.Session()
    
    try:
        # Establish session to grab JSESSIONID
        session.get("https://tgsouthernpower.org/onlinebillenquiry", timeout=10)

        # The new payload structure you discovered
        payload = {
            "inlineRadioOptions": request_data.radio_option,
            "ukscno": request_data.ukscno
        }

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://tgsouthernpower.org",
            "Referer": "https://tgsouthernpower.org/onlinebillenquiry",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        response = session.post(target_url, data=payload, headers=headers, allow_redirects=False, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        
        # Find the main data table
        table = soup.find("table", class_="table-bordered")
        if not table:
            raise HTTPException(status_code=404, detail="Billing table not found in the response.")

        # Initialize our nested JSON structure
        bill_data = {
            "consumer_details": {},
            "arrears": {},
            "current_month_bill": {},
            "total_payable": {},
            "total_paid": {}
        }
        
        # We will track which section we are currently parsing
        current_section = "consumer_details"

        for row in table.find_all("tr"):
            # 1. Check if this row is a dark blue section header (colspan="4")
            section_header = row.find("td", colspan="4")
            if section_header:
                section_text = section_header.text.strip().lower()
                # Update our current_section tracker based on the text
                if "arrears" in section_text:
                    current_section = "arrears"
                elif "current month" in section_text:
                    current_section = "current_month_bill"
                elif "payable" in section_text:
                    current_section = "total_payable"
                elif "paid :" in section_text: # Note the colon to distinguish from payable
                    current_section = "total_paid"
                continue # Skip to the next row now that we know the section

            # 2. Extract standard data rows
            ths = row.find_all("th")
            tds = row.find_all("td")
            
            # Use zip to pair up headers with data (handles 2 pairs per row perfectly)
            for th, td in zip(ths, tds):
                key = th.text.strip().replace(' ', '_').lower() # Format key cleanly
                value = td.text.strip()
                value = re.sub(r'\s+', ' ', value) # Clean up extra whitespace/newlines
                
                # Store it in the correct section dictionary
                bill_data[current_section][key] = value

        return {
            "status": "success",
            "data": bill_data
        }

    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed: {e}")
        raise HTTPException(status_code=502, detail="Failed to communicate with the utility server")