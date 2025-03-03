from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .qa_system import QASystem
import os

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

qa_system = QASystem()

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")

# Mount the static directory
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    return {"message": "Welcome to Confluence Chatbot API"}

@app.get("/widget")
async def get_widget():
    return FileResponse(os.path.join(static_dir, "widget.html"))

class Question(BaseModel):
    text: str

@app.post("/ask")
async def ask_question(question: Question):
    result = qa_system.get_answer(question.text)
    return result