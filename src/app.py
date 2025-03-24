from flask import Flask, jsonify, render_template, request
import os
from qa_system import QASystem

app = Flask(__name__, template_folder='Templates')
qa_system = QASystem()  # Initialize the QA system

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Confluence chatbot is running"
    })

@app.route('/widget')
def widget():
    return render_template('widget.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' field"}), 400
            
        question = data.get('text', '')
        print(f"Received question: {question}")
        
        # Use the QA system to get an answer
        result = qa_system.get_answer(question)
        
        return jsonify(result)
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e), "answer": "Sorry, I encountered an error processing your request."}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)