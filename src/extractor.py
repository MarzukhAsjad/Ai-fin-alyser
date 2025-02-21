"""
This module provides functionality to extract and process HTML content from URLs listed in a CSV file.
Functions:
    extract_content(soup: BeautifulSoup) -> Tuple[str, str]:
        Extracts the title and meaningful content (subtitles and paragraphs) from a BeautifulSoup object.
    parse_html_content(url: str, idx: int) -> str:
        Parses the HTML content of a given URL, extracts the title and meaningful content, and exports it to a .html file.
        Returns "Accessible" if the URL is processed successfully, otherwise returns "Not Accessible".
    process_csv(contents: bytes) -> str:
        Processes a CSV file containing URLs, extracts and exports the HTML content of each URL, and tracks the progress.
        Returns a string representation of the DataFrame with an added 'Accessibility' column indicating the status of each URL.
"""
import pandas as pd
from io import StringIO
import requests
from bs4 import BeautifulSoup

progress = {"total": 0, "processed": 0}

# Function to extract the title and meaningful content from a BeautifulSoup object
def extract_content(soup):
    title = soup.title.string if soup.title else "No Title"
    content = ""
    
    # Extract meaningful content (subtitles and paragraphs)
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
        content += tag.get_text() + "\n"
    
    return title, content

# Function to parse the HTML content of a URL
def parse_html_content(url: str, idx: int):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title, non_title_content = extract_content(soup)
        
        # Export meaningful content to a .html file
        html_filename = f"exported_html_{idx}.html"
        with open(html_filename, "w", encoding='utf-8') as html_file:
            html_file.write(f"<h1>{title}</h1>\n{non_title_content}")
        
        return "Accessible"
    except requests.exceptions.RequestException as e:
        print(f"Error processing URL {url}: {e}")
        return "Not Accessible"

# Function to process a CSV file containing URLs
def process_csv(contents: bytes) -> str:
    # The progress dictionary will be used to track the files processed
    global progress

    # Check if the contents are empty
    if not contents:
        print("Empty contents received")
        return "Empty contents received"
    
    # Read the CSV file
    df = pd.read_csv(StringIO(contents.decode('utf-8')))
    
    # Extract URLs from the DataFrame
    if 'URL' not in df.columns:
        print("No 'URL' column found in the CSV")
        return "No 'URL' column found in the CSV"
    
    # Convert the 'URL' column to a list
    urls = df['URL'].tolist()
    progress["total"] = len(urls)
    accessibility = []
    
    # Process each URL by calling the parse_html_content function, if fails, then URl is not accessible
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
