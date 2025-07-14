from fastapi import FastAPI, File, UploadFile

app = FastAPI()

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "content_type": file.content_type
    }

@app.post("/readfile/")
async def read_file(file: UploadFile = File(...)):
    content = await file.read()
    return {"content": content.decode("utf-8")}
