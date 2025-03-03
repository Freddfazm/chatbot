from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to Confluence Chatbot API"}

class Question(BaseModel):
    text: str

@app.post("/ask")
async def ask_question(question: Question):
    result = qa_system.get_answer(question.text)
    return result