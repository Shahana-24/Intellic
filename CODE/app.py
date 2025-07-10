from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from textblob import TextBlob
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = '123'


genai.configure(api_key="")  


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()



@app.route('/')
def home():
    return render_template("chat.html")

@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    password = request.form['password']
    if not User.query.filter_by(email=email).first():
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        session['user'] = email
    return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    user = User.query.filter_by(email=email, password=password).first()
    if user:
        session['user'] = email
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/chat', methods=['POST'])
def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment_score = blob.sentiment.polarity
    if sentiment_score > 0:
        sentiment_label = "Positive"
    elif sentiment_score < 0:
        sentiment_label = "Negative"
    else:
        sentiment_label = "Neutral"
    
    return sentiment_label, sentiment_score

# @app.route("/chatbot", methods=["POST"])
# def chatbot():
#     """Handles user messages and returns chatbot responses with sentiment analysis."""
#     data = request.get_json()
#     user_message = data.get("message", "")

#     # Analyze User Sentiment
#     sentiment_label, sentiment_score = analyze_sentiment(user_message)

#     # Generate AI Response using Gemini
#     model = genai.GenerativeModel("gemini-1.5-flash")
#     response = model.generate_content(user_message)

#     bot_reply = response.text if response.text else "I'm here to listen. Tell me more."

#     return jsonify({
#         "reply": bot_reply,
#         "sentiment": sentiment_label,
#         "sentiment_score": sentiment_score
#     })

@app.route("/chatbot", methods=["POST"])
def chatbot():
    """Handles user messages and returns chatbot responses with sentiment and mood analysis."""
    data = request.get_json()
    user_message = data.get("message", "")

    
    sentiment_label, sentiment_score = analyze_sentiment(user_message)

    
    lowered = user_message.lower()
    if "happy" in lowered or sentiment_score > 0.5:
        mood = "Joyful"
    elif "sad" in lowered or sentiment_score < -0.5:
        mood = "Sad"
    elif "angry" in lowered:
        mood = "Angry"
    elif any(word in lowered for word in ["anxious", "worried", "nervous"]):
        mood = "Anxious"
    elif "excited" in lowered:
        mood = "Excited"
    else:
        mood = "Calm"

    
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(user_message)

    bot_reply = response.text if response.text else "I'm here to listen. Tell me more."

    return jsonify({
        "reply": bot_reply,
        "sentiment": sentiment_label,
        "sentiment_score": sentiment_score,
        "mood": mood
    })



if __name__ == '__main__':
    app.run(debug=True)
