from fastapi import FastAPI
from pydantic import BaseModel
from src.qa_system import QASystem  # Import the class, not an object
# Create an instance of the QASystem class

app = FastAPI()
qa_system = QASystem()


@app.get("/")
def read_root():
    return {"message": "Welcome to Confluence Chatbot API"}

class Question(BaseModel):
    text: str

@app.post("/ask")
async def ask_question(question: Question):
    result = qa_system.get_answer(question.text)
    return result