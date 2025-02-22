from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import StreamingResponse, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .extractor import process_csv_sync, print_data_to_file
from .causal import read_csv_extract_corpora, store_correlation_scores
from .neo4j_connector import Neo4jConnector
from .nlp_processor import compare_corpora
import logging
import os
import math

app = FastAPI()

# Initialize the rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Add exception handler for rate limit exceeded
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
    )

@app.get("/")
@limiter.limit("20/second")
def read_root(request: Request):
    return {"Hello": "World"}

# Endpoint to upload CSV files and stream progress updates
@app.post("/upload/")
@limiter.limit("3/second")
async def upload_csv(request: Request, file: UploadFile = File(...)):
    try:
        # Check if the uploaded file is a CSV
        if file.filename.endswith('.csv'):
            contents = await file.read()
            
            # Stream the progress updates
            return StreamingResponse(process_csv_sync(contents), media_type="text/plain")
        else:
            return {"error": "File is not a CSV"}
    except Exception as e:
        logging.error(f"Error: {e}")
        return {"error": str(e)}

# Endpoint to print the DataFrame to a .txt file
@app.get("/print-data/")
@limiter.limit("5/second")
def print_data(request: Request):
    result = print_data_to_file()
    return {"message": result}

# Endpoint to find correlation between all available corpora
@app.get("/calculate-correlation/")
@limiter.limit("3/second")
def calculate_correlation(request: Request):
    # Ensure the file path is correctly referenced
    file_path = "printed_data.csv"
    print("File path:", file_path)
    read_csv_extract_corpora(file_path)
    store_correlation_scores()
    return {"message": "Correlation calculation completed and ready for querying."}

# Endpoint to query the Neo4j database by title
@app.get("/query-by-title/")
@limiter.limit("5/second")
def query_by_title(request: Request, title: str):
    connector = Neo4jConnector()
    result = connector.query_by_title(title)
    connector.close()
    return {"result": result}

# Endpoint to test the connection to the Neo4j database
@app.get("/test-connection/")
@limiter.limit("5/second")
def test_connection(request: Request):
    connector = Neo4jConnector()
    success = connector.test_connection()
    connector.close()
    return {"connection_successful": success}

# Endpoint to query all the correlations in the database
@app.get("/query-all-correlations/")
@limiter.limit("5/second")
def query_all_correlations(request: Request):
    connector = Neo4jConnector()
    result = connector.query_all_correlations()
    connector.close()
    
    # Sanitize correlation values
    sanitized = []
    for record in result:
        corr = record.get("correlation")
        if corr is not None and math.isfinite(corr):
            corr = round(corr, 5)
        # Replace non-finite correlation with None
        if corr is None or not math.isfinite(corr):
            record["correlation"] = None
        sanitized.append(record)
        
    return {"result": sanitized}

# Endpoint to query pairwise causal relationships
@app.get("/query-pairwise-causal/")
@limiter.limit("5/second")
def get_pairwise_causal(request: Request):
    connector = Neo4jConnector()
    result = connector.query_pairwise_causal()
    connector.close()
    return {"result": result}

# Endpoint to query the top N causal relationships
@app.get("/query-highest-correlation/")
@limiter.limit("5/second")
def get_highest_correlation(request: Request, n = 1):
    connector = Neo4jConnector()
    result = connector.query_highest_correlation(n)
    connector.close()
    return {"result": result}

# This endpoint will clear all data in the Neo4j database
@app.delete("/clear-database/")
@limiter.limit("1/second")
def clear_database(request: Request):
    connector = Neo4jConnector()
    connector.clear_database()
    connector.close()
    return {"message": "Database cleared."}

# This query will test the compare_corpora function from the nlp_processor module
@app.get("/test-compare-corpora/")
@limiter.limit("1/second")
def test_compare_corpora(request: Request):
    corpus1 = "This is a test corpus for comparison."
    corpus2 = "This is another test corpus for comparison."
    result = compare_corpora(corpus1, corpus2)
    return {"correlation": result}
# The queries will be: pairwise causal relationship, top N causal relationships, and all causal relationships
# The results will be returned as JSON responses