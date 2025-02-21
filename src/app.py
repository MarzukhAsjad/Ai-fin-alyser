from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import StreamingResponse, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .extractor import process_csv_sync, print_data_to_file
from .causal import read_csv_extract_corpora, store_correlation_scores
import logging
import os

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
    file_path = os.path.join(os.path.dirname(__file__), "..", "..", "printed_data.csv")
    print("File path:", file_path)
    read_csv_extract_corpora(file_path)
    store_correlation_scores("bolt://localhost:7687", "neo4j", "password")
    return {"message": "Correlation calculation completed and ready for querying."}