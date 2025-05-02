from flask import Flask, request, jsonify
from deployment.src.model import ask, check_question_feedback
from deployment.src.feedback_handler import save_feedback

app = Flask(__name__)

@app.route("/")
def root():
    return "Instant Immigration Bot API is running."

@app.route("/ask", methods=["POST"])
def handle_question():
    data = request.json
    query = data.get("query")
    user_id = data.get("user_id", "anonymous")

    if not query:
        return jsonify({"error": "No query provided"}), 400

    result = check_question_feedback(query, user_id)
    
    if result["is_feedback"]:
        last_qna = result["last_qna"]
        if not last_qna["question"]:
            return jsonify({"message": "Sorry, please ask a question first before providing feedback."}), 400

        save_result = save_feedback(result["feedback_obj"], last_qna)
        return jsonify({"message": save_result}), 200

    answer = ask(query, user_id)
    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)