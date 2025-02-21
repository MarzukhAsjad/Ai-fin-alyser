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
import httpx
from bs4 import BeautifulSoup
from .nlp_processor import make_summary
import asyncio

progress = {"total": 0, "processed": 0}

# Function to extract the title and meaningful content from a BeautifulSoup object
def extract_content(soup):
    title = soup.title.string if soup.title else "No Title"
    content = ""
    
    # Extract meaningful content (subtitles and paragraphs)
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
        content += tag.get_text() + "\n"
    
    return title, content

# Asynchronous function to parse the HTML content of a URL
async def parse_html_content(url: str):
    async with httpx.AsyncClient() as client:
        try:
            # Send a GET request to the URL
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title and content
            title, non_title_content = extract_content(soup)
            
            # Generate summary using make_summary
            summary = make_summary(non_title_content)
            
            return title, non_title_content, summary, "Accessible"
        except httpx.RequestError as e:
            print(f"Error processing URL {url}: {e}")
            return None, None, None, "Not Accessible"

# Asynchronous function to process a CSV file containing URLs
async def process_csv(contents: bytes) -> str:
    global progress

    # Check if the contents are empty
    if not contents:
        print("Empty contents received")
        return "Empty contents received"
    
    # Read the CSV file
    df = pd.read_csv(StringIO(contents.decode('utf-8')))
    
    # Check if 'URL' column exists
    if 'URL' not in df.columns:
        print("No 'URL' column found in the CSV")
        return "No 'URL' column found in the CSV"
    
    # Extract URLs from the DataFrame
    urls = df['URL'].tolist()
    progress["total"] = len(urls)
    accessibility = []
    titles = []
    contents = []
    summaries = []
    
    # Create tasks to process each URL
    tasks = [parse_html_content(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    for result in results:
        if isinstance(result, Exception):
            title, content, summary, accessibility_status = None, None, None, "Not Accessible"
        else:
            title, content, summary, accessibility_status = result
        titles.append(title)
        contents.append(content)
        summaries.append(summary)
        accessibility.append(accessibility_status)
        progress["processed"] += 1
    
    # Add new columns to the DataFrame
    df['Title'] = titles
    df['Content'] = contents
    df['Summary'] = summaries
    df['Accessibility'] = accessibility
    
    # Export the data to a .txt file
    with open("exported_data.txt", "w", encoding="utf-8") as txt_file:
        txt_file.write(df.to_string())
    
    # Reset progress to 0 after completion
    progress = {"total": 0, "processed": 0}
    
    global df_global
    df_global = df
    
    return df.to_string()

# Wrapper function to run the asynchronous process_csv function
def process_csv_sync(contents: bytes) -> str:
    return asyncio.run(process_csv(contents))

# Function to print the DataFrame to a .txt file
def print_data_to_file():
    global df_global
    if df_global is not None:
        with open("printed_data.txt", "w", encoding="utf-8") as txt_file:
            txt_file.write(df_global.to_string())
        return "Data printed to printed_data.txt"
    else:
        return "No data available to print"