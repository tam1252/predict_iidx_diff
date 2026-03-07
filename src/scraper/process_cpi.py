import json
import pandas as pd
import os

OUTPUT_DIR = "data/raw"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "cpi_scores.csv")
RAW_JSON_FILE = os.path.join(OUTPUT_DIR, "cpi_scores_raw.json")

# Browser Subagent returned this data, we will load it and convert it.
# As the data is large, we should read it from a saved json file to avoid clutter.
# For simplicity in this script, we'll read from cpi_scores_raw.json 

def process_cpi_data():
    with open('data/raw/cpi_raw_dump.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # data is a dict: {'headers': [...], 'result': [...]}
    df = pd.DataFrame(data['result'], columns=[h.lower() for h in data['headers']])
    
    # Clean up any potential formatting issues
    for col in ['easy', 'clear', 'hard', 'exhard', 'fc']:
        if col in df.columns:
            # Convert to float, coercing errors to NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"Successfully processed {len(df)} songs and saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_cpi_data()
