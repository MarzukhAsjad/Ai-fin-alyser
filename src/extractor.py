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
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

progress = {"total": 0, "processed": 0}
df_global = None  # Global variable to store the DataFrame

# Function to extract the title and meaningful content from a BeautifulSoup object
def extract_content(soup):
    title = soup.title.string if soup.title else "No Title"
    content = ""
    
    # Extract meaningful content (subtitles and paragraphs)
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
        content += tag.get_text() + "\n"
    
    return title, content

# Asynchronous function to parse the HTML content of a URL and put the result in a queue
async def parse_html_content(url: str, queue: asyncio.Queue, idx: int, ratio=0.1):
    async with httpx.AsyncClient() as client:
        try:
            # Send a GET request to the URL
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title and content
            title, non_title_content = extract_content(soup)
            
            # Generate summary using make_summary
            summary = make_summary(non_title_content, ratio)
            
            await queue.put((idx, title, non_title_content, summary, "Accessible"))
        except httpx.RequestError as e:
            print(f"Error processing URL {url}: {e}")
            await queue.put((idx, "No Title", "", "", "Not Accessible"))

# Asynchronous function to process a CSV file containing URLs and yield progress updates
async def process_csv(contents: bytes, ratio=0.1):
    global df_global

    try:
        # Check if the contents are empty
        if not contents:
            yield "Empty contents received\n"
            return
        
        # Read the CSV file
        df = pd.read_csv(StringIO(contents.decode('utf-8')))
        
        # Check if 'URL' column exists
        if 'URL' not in df.columns:
            yield "No 'URL' column found in the CSV\n"
            return
        
        # Extract URLs from the DataFrame
        urls = df['URL'].tolist()
        total = len(urls)
        processed = 0
        accessibility = [None] * total
        titles = [None] * total
        contents = [None] * total
        summaries = [None] * total
        
        # Create an asyncio.Queue to collect results
        queue = asyncio.Queue()
        
        # Create tasks to process each URL
        tasks = [parse_html_content(url, queue, idx, ratio) for idx, url in enumerate(urls)]
        
        # Process results as they are put in the queue
        for task in asyncio.as_completed(tasks):
            try:
                await task
                idx, title, content, summary, accessibility_status = await queue.get()
                titles[idx] = title
                contents[idx] = content
                summaries[idx] = summary
                accessibility[idx] = accessibility_status
            except Exception as e:
                logging.error(f"Error during processing: {e}")
                titles[idx] = "No Title"
                contents[idx] = ""
                summaries[idx] = ""
                accessibility[idx] = "Not Accessible"
            finally:
                processed += 1
                update_message = f"Processed {processed}/{total}\n"
                logging.info(update_message)
                yield update_message
        
        # Add new columns to the DataFrame
        df['Title'] = titles
        df['Content'] = contents
        df['Summary'] = summaries
        df['Accessibility'] = accessibility
        
        # Store the DataFrame in the global variable
        df_global = df
        
        completion_message = "Processing complete\n"
        logging.info(completion_message)
        yield completion_message
    except asyncio.CancelledError:
        logging.warning("Processing was cancelled")
        yield "Processing was cancelled\n"
    except Exception as e:
        logging.error(f"Error during processing: {e}")
        yield f"Error during processing: {e}\n"

# Wrapper function to run the asynchronous process_csv function
def process_csv_sync(contents: bytes, ratio=0.1):
    async def async_process():
        async for update in process_csv(contents, ratio):
            yield update
    return async_process()

# Function to print the DataFrame to a .csv file
def print_data_to_file():
    global df_global
    if df_global is not None:
        df_global.to_csv("printed_data.csv", index=False, encoding="utf-8")
        return "Data printed to printed_data.csv"
    else:
        return "No data available to print"