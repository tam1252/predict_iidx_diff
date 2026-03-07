import json
import pandas as pd
import os
from playwright.sync_api import sync_playwright

URL = "https://cpi.makecir.com/scores"
OUTPUT_DIR = "data/raw"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "cpi_scores.csv")

def scrape_cpi():
    print(f"Scraping {URL} using Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle")

        # Wait for the table to appear
        page.wait_for_selector("table#scores-index")

        data = page.evaluate('''() => {
            // Some DataTables allow setting length to -1 to show all rows
            try {
                // If it's a jQuery DataTable
                if (window.$ && $.fn.dataTable) {
                    $('#scores-index').DataTable().page.len(-1).draw();
                }
            } catch (e) {}

            let result = [];
            document.querySelectorAll('table#scores-index tbody tr').forEach(tr => {
                let cols = tr.querySelectorAll('td');
                if (cols.length >= 2) {
                    // Try to guess columns by headers, or just grab all text
                    // Typically: 
                    // cols[1] might be title
                    // cols[0]-cols[6] might be different things.
                    let rowData = [];
                    cols.forEach(td => rowData.push(td.innerText.trim()));
                    result.push(rowData);
                }
            });
            // Also grab headers
            let headers = [];
            document.querySelectorAll('table#scores-index thead th').forEach(th => headers.push(th.innerText.trim()));
            return {headers, result};
        }''')
        
        browser.close()

    headers = data['headers']
    rows = data['result']
    
    print(f"Extracted headers: {headers}")
    print(f"Extracted rows: {len(rows)}")
    
    # Save the raw output for inspection
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "cpi_raw_dump.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scrape_cpi()
