from io import BytesIO
from typing import List

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from Bot import Bot, OPENAI_API_KEY, OpenAIAPI
from VectorStore import VectorStore




app = FastAPI()
import asyncio


class AnswerQueryRequest(BaseModel):
    question: str
    k: int = 2


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
vectorStore = VectorStore("vector_store.pkl")
userId = "user1"
openai_api = OpenAIAPI(OPENAI_API_KEY)
bot = Bot(openai_api, vectorStore)





async def get_answer(userId: str, question: str, k: int = 2):
    return await bot.getAnswer(userId, question, k)


import uuid
import os
from pathlib import Path


# @app.post("/upload_documents/")
# async def upload_documents(files: List[UploadFile] = File()):
#     for file in files:
#         content = await file.read()
#         file_id = uuid.uuid4()
#         file_extension = Path(file.filename).suffix
#         user_folder = f"Docs/{userId}"
#         os.makedirs(user_folder, exist_ok=True)
#         file_path = os.path.join(user_folder, f"{file_id}{file_extension}")
#         print(file_path)
#         with open(file_path, "wb") as f:
#             f.write(content)
#         bot.digestDoc(userId, file_path, file_id)
#     return {"status": "Documents uploaded", "filenames": [file.filename for file in files],
#             "content_types": [file.content_type for file in files]}


from pyngrok import ngrok, conf
from config import NGROK_AUTH_TOKEN
@app.on_event("startup")
async def startup_event():
    # Set the ngrok authentication token
    auth_token = NGROK_AUTH_TOKEN
    ngrok_config = conf.PyngrokConfig(auth_token=auth_token)
    conf.set_default(ngrok_config)

    # Start the ngrok tunnel to make the api public on internet
    ngrok_tunnel = ngrok.connect(7860)
    print('Public URL:', ngrok_tunnel.public_url)

@app.post("/upload_documents/")
async def upload_documents(files: List[UploadFile] = File()):
    for file in files:
        content = await file.read()
        file_id = uuid.uuid4()
        file_extension = Path(file.filename).suffix
        user_folder = os.path.join("Docs", userId)
        os.makedirs(user_folder, exist_ok=True)
        file_path = os.path.join(user_folder, f"{file_id}{file_extension}")

        print(file_path)
        with open(file_path, "wb") as f:
            f.write(content)
        bot.digestDoc(userId, str(file_path), file_id)
    return {"status": "Documents uploaded", "filenames": [file.filename for file in files],
            "content_types": [file.content_type for file in files]}


@app.get("/get_answer/")
async def get_answer_endpoint(question: str, k: int = 2):
    answer = await get_answer(userId, question, k)
    return JSONResponse(content=answer)


from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse


@app.get("/")
async def serve_file(request: Request):
    file_path = request.query_params.get("file")
    if file_path and os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")
