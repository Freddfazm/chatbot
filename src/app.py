from flask import Flask, jsonify, render_template, request
import os
import json

app = Flask(__name__, template_folder='Templates')

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Confluence chatbot is running"
    })

@app.route('/widget')
def widget():
    return render_template('widget.html')

@app.route('/ask', methods=['POST', 'OPTIONS'])
def ask():
    if request.method == 'OPTIONS':
        return '', 200
        
    # Add debug printing
    print("Received request at /ask")
    print(f"Request data: {request.data}")
    
    try:
        data = request.json
        print(f"Parsed JSON: {data}")
        
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' field"}), 400
            
        question = data.get('text', '')
        print(f"Question: {question}")
        
        return jsonify({
            "answer": f"You asked: {question}"
        })
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500
        
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 