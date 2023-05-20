from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from Bot import Bot, OPENAI_API_KEY, OpenAIAPI
from VectorStore import VectorStore
import asyncio


class AnswerQueryRequest(BaseModel):
    question: str
    k: int = 2


app = FastAPI()
vectorStore = VectorStore("Persistence/vector_store.pkl")
userId = "user1"
openai_api = OpenAIAPI(OPENAI_API_KEY)
bot = Bot(openai_api, vectorStore)


async def get_answer(userId: str, question: str, k: int = 2):
    return await bot.getAnswer(userId, question, k)


@app.post("/upload_document/")
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    bot.digestDoc(userId, content)
    return {"status": "Document uploaded"}


@app.get("/get_answer/")
async def get_answer_endpoint(question: str, k: int = 2):
    answer = await get_answer(userId, question, k)
    return JSONResponse(content=answer)
