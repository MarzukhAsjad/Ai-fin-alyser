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
from ..utils.nlp_processor import make_summary
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

progress = {"total": 0, "processed": 0, "error_processed": 0}
df_global = None  # Global variable to store the DataFrame

# Function to extract the title and meaningful content from a BeautifulSoup object
def extract_content(soup):
    title = soup.title.string if soup.title else None
    content = ""
    
    # Extract meaningful content (subtitles and paragraphs)
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
        content += tag.get_text() + "\n"
    
    # Validate content
    if not title or not content.strip():
        raise ValueError("No meaningful content found in the article")
    
    return title, content

# Asynchronous function to parse the HTML content of a URL and put the result in a queue
async def parse_html_content(url: str, queue: asyncio.Queue, idx: int, ratio=0.1, max_sentences=10):
    async with httpx.AsyncClient() as client:
        try:
            # Send a GET request to the URL
            response = await client.get(url)
            response.raise_for_status()
            
            # Check if response has content
            if not response.content:
                raise ValueError("Empty response received")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title and content (will raise ValueError if empty)
            title, non_title_content = extract_content(soup)
            
            # Generate summary using make_summary
            summary = make_summary(non_title_content, ratio, max_sentences)
            
            # Validate summary
            if not summary:
                raise ValueError("Could not generate summary from content")
            
            await queue.put((idx, title, non_title_content, summary, "Accessible"))
            
        except (httpx.RequestError, ValueError) as e:
            logging.error(f"Error processing URL {url}: {e}")
            await queue.put((idx, "No Title", "", "", "Not Accessible"))
        except Exception as e:
            logging.error(f"Unexpected error processing URL {url}: {e}")
            await queue.put((idx, "No Title", "", "", "Not Accessible"))

# Asynchronous function to process a CSV file containing URLs and yield progress updates
async def process_csv(contents: bytes, ratio=0.1, max_sentences=10):
    global df_global

    try:
        # Check if the contents are empty
        if not contents:
            yield '{"status": "error", "message": "Empty contents received"}\n'
            return
        
        # Read the CSV file
        df = pd.read_csv(StringIO(contents.decode('utf-8')))
        
        # Check if 'URL' column exists
        if 'URL' not in df.columns:
            yield '{"status": "error", "message": "No URL column found in the CSV"}\n'
            return
        
        # Extract URLs from the DataFrame
        urls = df['URL'].tolist()
        total = len(urls)
        processed = 0
        error_processed = 0
        # Preallocate lists to hold row data
        accessibility = [None] * total
        titles = [None] * total
        contents_list = [None] * total
        summaries = [None] * total
        
        # Create an asyncio.Queue to collect results
        queue = asyncio.Queue()
        
        # Create tasks to process each URL
        tasks = [parse_html_content(url, queue, idx, ratio, max_sentences) for idx, url in enumerate(urls)]
        
        # Process tasks as they complete
        pending_tasks = set(tasks)
        while pending_tasks:
            done, pending_tasks = await asyncio.wait(
                pending_tasks, 
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for completed_task in done:
                try:
                    await completed_task
                    idx, title, content, summary, accessibility_status = await queue.get()
                    titles[idx] = title
                    contents_list[idx] = content
                    summaries[idx] = summary
                    accessibility[idx] = accessibility_status
                    if accessibility_status != "Accessible":
                        error_processed += 1
                except Exception as e:
                    logging.error(f"Error during processing task: {e}")
                    error_processed += 1
                finally:
                    processed += 1
                    update_message = (
                        f'{{"status": "processing", "total": {total}, '
                        f'"processed": {processed}, "errors": {error_processed}}}\n'
                    )
                    logging.info(update_message)
                    yield update_message
        
        # Add new columns to the DataFrame
        df['Title'] = titles
        df['Content'] = contents_list
        df['Summary'] = summaries
        df['Accessibility'] = accessibility
        
        # Store the DataFrame in the global variable
        df_global = df
        
        # Generate completion message
        completion_message = (
            f'{{"status": "complete", "message": "Processing complete", '
            f'"total": {total}, "processed": {processed}, "errors": {error_processed}}}\n'
        )
        logging.info(completion_message.strip())
        
        # Call print_data_to_file after completion
        print_result = print_data_to_file()
        final_message = completion_message.rstrip('\n')[:-1] + f', "file_status": "{print_result}"' + '}\n'
        
        yield final_message

    except asyncio.CancelledError:
        yield '{"status": "cancelled", "message": "Processing was cancelled"}\n'
    except Exception as e:
        error_message = f'{{"status": "error", "message": "Error during processing: {str(e)}"}}\n'
        logging.error(error_message)
        yield error_message

# Wrapper function to run the asynchronous process_csv function
def process_csv_sync(contents: bytes, ratio=0.1, max_sentences=10):
    async def async_process():
        async for update in process_csv(contents, ratio, max_sentences):
            yield update
            # No need to call print_data_to_file here as it's already called in process_csv
    return async_process()

# Function to print the DataFrame to a .csv file
def print_data_to_file():
    global df_global
    if df_global is not None:
        df_global.to_csv("printed_data.csv", index=False, encoding="utf-8")
        return "Data printed to printed_data.csv"
    else:
        return "No data available to print"
    
def return_df_as_csv():
    global df_global
    if df_global is not None:
        return df_global.to_csv(index=False, encoding="utf-8")
    else:
        return "No data available to return"