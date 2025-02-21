# Ai-fin-alyser

This tool will analyse CSVs, extract articles from the CSVs, visualize the causal relationship between the content of the articles and then cluster the modules into distint classes accordingly. The tool now will have a REST API to perform all these functions.

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

This will upload the CSV file and start processing in the background.

## Get the status of the processing

```bash
curl -X GET "http://localhost:8000/progress" -H "accept: application/json"
```

This will return the status of the processing in json form:

```json
{
  "total": 30,
  "processed": 17
}
```

thus indicating that 17 out of 30 articles have been processed so far.