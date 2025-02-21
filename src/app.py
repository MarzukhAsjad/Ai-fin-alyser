from fastapi import FastAPI, UploadFile, File
from .extractor import process_csv

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# This endpoint will be used to upload CSV files
@app.post("/upload/")
async def upload_csv(file: UploadFile = File(...)):
    contents = await file.read()
    table = process_csv(contents)
    
    return {"message": "CSV uploaded and processed successfully", "table": table}