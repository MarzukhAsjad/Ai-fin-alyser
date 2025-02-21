from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from .extractor import process_csv_sync, print_data_to_file
import logging

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# Endpoint to upload CSV files and stream progress updates
@app.post("/upload/")
async def upload_csv(file: UploadFile = File(...)):
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
def print_data():
    result = print_data_to_file()
    return {"message": result}
