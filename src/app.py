from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from services.extractor import process_csv_sync, return_df_as_csv
from services.causal import (read_csv_extract_corpora, store_correlation_scores,
                     query_corpus_by_title, query_all_correlations, 
                     query_pairwise_causal, query_highest_correlation,
                     clear_correlation_database, test_db_connection, store_correlation_scores_stream)
from services.cluster import run_hierarchical_clustering, run_lda_clustering
import logging
import math
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
            return StreamingResponse(process_csv_sync(contents)(), media_type="text/plain")
        else:
            return {"error": "File is not a CSV"}
    except Exception as e:
        logging.error(f"Error: {e}")
        return {"error": str(e)}

# Endpoint to print the DataFrame to a .txt file
@app.get("/view-data/")
@limiter.limit("5/second")
def print_data(request: Request):
    result = return_df_as_csv()
    return Response(result, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=output_data.csv"})

# Endpoint to find correlation between all available corpora
@app.get("/calculate-correlation/")
@limiter.limit("3/second")
def calculate_correlation(request: Request):
    # Ensure the file path is correctly referenced
    file_path = "printed_data.csv"
    read_csv_extract_corpora(file_path)
    # Return a streaming response with progress updates
    return StreamingResponse(store_correlation_scores_stream(), media_type="text/plain")

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

########################################
###### Cluster Analysis Endpoints ######
########################################

# Endpoint to run hierarchical clustering
@app.get("/run-hierarchical-clustering/")
@limiter.limit("3/second")
def hierarchical_clustering_endpoint(request: Request):
    run_hierarchical_clustering()
    return {"message": "Hierarchical clustering completed."}

@app.get("/download-hierarchical-clustering-image/")
@limiter.limit("5/second")
def get_clustering_image(request: Request):
    image_path = "hierarchical_clustering.png"
    abs_path = os.path.abspath(image_path)
    
    logger.debug(f"Looking for clustering image at: {abs_path}")
    
    if os.path.exists(abs_path):
        logger.info(f"Found clustering image at: {abs_path}")
        return FileResponse(abs_path, media_type="image/png", filename="hierarchical_clustering.png")
    
    logger.error(f"Clustering image not found at: {abs_path}")
    logger.debug(f"Current working directory: {os.getcwd()}")
    logger.debug(f"Directory contents: {os.listdir('.')}")
    
    return JSONResponse(
        status_code=404,
        content={"error": f"Clustering image not found at {abs_path}"}
    )

# This endpoint will be used to run LDA clustering
@app.get("/run-lda-clustering/")
@limiter.limit("1/second")
def lda_clustering_endpoint(request: Request):
    try:
        run_lda_clustering()
        return {"message": "LDA clustering completed."}
    except Exception as e:
        logger.error(f"Error in LDA clustering: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error in LDA clustering: {e}"}
        )

# This endpoint will return the png from lda clustering
@app.get("/download-lda-clustering-image/")
@limiter.limit("5/second")
def get_lda_clustering_image(request: Request):
    image_path = "lda_clusters.png"
    abs_path = os.path.abspath(image_path)
    
    logger.debug(f"Looking for clustering image at: {abs_path}")
    
    if os.path.exists(abs_path):
        logger.info(f"Found clustering image at: {abs_path}")
        return FileResponse(abs_path, media_type="image/png", filename="lda_clusters.png")
    
    logger.error(f"Clustering image not found at: {abs_path}")
    logger.debug(f"Current working directory: {os.getcwd()}")
    logger.debug(f"Directory contents: {os.listdir('.')}")
    
    return JSONResponse(
        status_code=404,
        content={"error": f"Clustering image not found at {abs_path}"}
    )