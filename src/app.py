from flask import Flask, jsonify, render_template, request

app = Flask(__name__, template_folder='Templates')

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
    data = request.json
    question = data.get('text', '')
    return jsonify({
        "answer": f"You asked: {question}"
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
