import pandas as pd
from io import StringIO
import requests
from bs4 import BeautifulSoup

progress = {"total": 0, "processed": 0}

def process_csv(contents: bytes) -> str:
    global progress
    if not contents:
        print("Empty contents received")
        return "Empty contents received"
    
    df = pd.read_csv(StringIO(contents.decode('utf-8')))
    
    # Extract URLs from the DataFrame
    if 'URL' not in df.columns:
        print("No 'URL' column found in the CSV")
        return "No 'URL' column found in the CSV"
    
    urls = df['URL'].tolist()
    progress["total"] = len(urls)
    accessibility = []
    
    for idx, url in enumerate(urls):
        print(f"Processing URL: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            raw_html = soup.prettify()
            
            # Export raw HTML to a .html file
            html_filename = f"exported_html_{idx}.html"
            with open(html_filename, "w", encoding='utf-8') as html_file:
                html_file.write(raw_html)
            
            accessibility.append("Accessible")
        except requests.exceptions.RequestException as e:
            print(f"Error processing URL {url}: {e}")
            accessibility.append("Not Accessible")
        
        progress["processed"] += 1
    
    # Add accessibility column to the DataFrame
    df['Accessibility'] = accessibility
    
    # Export the data to a .txt file
    with open("exported_data.txt", "w") as txt_file:
        txt_file.write(df.to_string())
    
    return df.to_string()
