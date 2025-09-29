from flask import Flask, jsonify, render_template
import json

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("1.html")

@app.route("/questions")
def get_questions():
    with open("1.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    return jsonify(questions)

if __name__ == "__main__":
    app.run(debug=True)
