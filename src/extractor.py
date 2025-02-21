import pandas as pd
from io import StringIO
import requests
from bs4 import BeautifulSoup

progress = {"total": 0, "processed": 0}

def extract_non_title_content(soup):
    title = soup.title.string if soup.title else "No Title"
    content = ""
    
    # Extract meaningful content (subtitles and paragraphs)
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
        content += tag.get_text() + "\n"
    
    return title, content

def parse_html_content(url: str, idx: int):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title, non_title_content = extract_non_title_content(soup)
        
        # Export meaningful content to a .html file
        html_filename = f"exported_html_{idx}.html"
        with open(html_filename, "w", encoding='utf-8') as html_file:
            html_file.write(f"<h1>{title}</h1>\n{non_title_content}")
        
        return "Accessible"
    except requests.exceptions.RequestException as e:
        print(f"Error processing URL {url}: {e}")
        return "Not Accessible"

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
        accessibility_status = parse_html_content(url, idx)
        accessibility.append(accessibility_status)
        progress["processed"] += 1
    
    # Add accessibility column to the DataFrame
    df['Accessibility'] = accessibility
    
    # Export the data to a .txt file
    with open("exported_data.txt", "w") as txt_file:
        txt_file.write(df.to_string())
    
    # Reset progress to 0 after completion
    progress = {"total": 0, "processed": 0}
    
    return df.to_string()
