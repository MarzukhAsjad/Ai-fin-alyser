# Ai-fin-alyser

This tool will analyse CSVs, extract articles from the CSVs, visualize the causal relationship between the content of the articles and then cluster the modules into distinct classes accordingly. The tool now will have a REST API to perform all these functions.

# Installation instructions
## Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

## Install the requirements

```bash
pip install -r requirements.txt
```

## Run the application

```bash
uvicorn src.app:app --reload
```

# Usage

## Upload a CSV file

```bash
curl -X POST "http://localhost:8000/upload" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@/path/to/your/file.csv"
```

This will upload the CSV file and start processing. The endpoint will stream back the processing rate in text form.

```text
Processed 1/30
Processed 2/30
Processed 3/30
...
Processed 29/30
Processed 30/30
Processing complete
```

## Print the dataframe

This endpoint will print the dataframe that was created with the title, content and summary of the articles.

```bash
curl -X GET "http://localhost:8000/print-data" -H "accept: application/json"
```

# Features

## Initial summarisation tool

The summarization tool leverages the Natural Language Toolkit (nltk) to generate concise summaries of text. The `make_summary` function processes the text by tokenizing it into sentences and words, removing stop words, and calculating word frequencies. Sentences are then scored based on the frequency of their words. The function selects the top sentences according to their scores to form the summary. The length of the summary can be adjusted using the `ratio` parameter, which determines the proportion of sentences to include, and the `max_sentences` parameter, which sets an upper limit on the number of sentences in the summary.

## Rate limiting

The application implements rate limiting using the `slowapi` library to control the number of requests a unique IP address can make to the API endpoints. This helps to prevent abuse and ensures fair usage of the API.

## Asynchronous fast processing

The application uses FastAPI's asynchronous capabilities to process CSV files quickly and efficiently. The `upload` endpoint processes the CSV file asynchronously, allowing the user to continue interacting with the API while the file is being processed. The processing rate is streamed back to the user in real-time, providing feedback on the progress of the operation. By using asynchronous processing, the duration for processing large CSV files is significantly reduced, improving the user experience.

## Task queue with asyncio.Queue

The application uses `asyncio.Queue` to manage tasks efficiently. This queue allows the application to handle multiple tasks concurrently without blocking the main thread. When a CSV file is uploaded, tasks are added to the queue and processed asynchronously. This ensures that the application remains responsive and can handle multiple file uploads simultaneously while retaining the sequential order of processing.