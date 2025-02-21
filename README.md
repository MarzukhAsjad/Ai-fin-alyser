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