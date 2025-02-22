from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import StreamingResponse, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .extractor import process_csv_sync, print_data_to_file
from .causal import (read_csv_extract_corpora, store_correlation_scores,
                     query_corpus_by_title, query_all_correlations, 
                     query_pairwise_causal, query_highest_correlation,
                     clear_correlation_database, test_db_connection)
import logging
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

@app.get("/query-by-title/")
@limiter.limit("5/second")
def query_by_title(request: Request, title: str):
    result = query_corpus_by_title(title)
    return {"result": result}

@app.get("/query-all-correlations/")
@limiter.limit("5/second")
def query_all_correlations_endpoint(request: Request):
    result = query_all_correlations()
    # Sanitize correlation values as before
    sanitized = []
    for record in result:
        corr = record.get("correlation")
        if corr is not None and math.isfinite(corr):
            corr = round(corr, 5)
        if corr is None or not math.isfinite(corr):
            record["correlation"] = None
        sanitized.append(record)
    return {"result": sanitized}

@app.get("/query-pairwise-causal/")
@limiter.limit("5/second")
def get_pairwise_causal(request: Request):
    result = query_pairwise_causal()
    return {"result": result}

@app.get("/query-highest-correlation/")
@limiter.limit("5/second")
def get_highest_correlation(request: Request, limit: int = 1):
    result = query_highest_correlation(limit)
    return {"result": result}

@app.delete("/clear-database/")
@limiter.limit("1/second")
def clear_database(request: Request):
    message = clear_correlation_database()
    return {"message": message}

@app.get("/test-connection/")
@limiter.limit("5/second")
def test_connection(request: Request):
    success = test_db_connection()
    return {"connection_successful": success}