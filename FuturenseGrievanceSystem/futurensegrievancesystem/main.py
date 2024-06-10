from flask import Flask, request, jsonify, render_template
import sqlite3
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import random

nltk.download('stopwords')
nltk.download('punkt')

app = Flask(__name__)

ticket_numbers = []

def connect_database():
    conn = sqlite3.connect('grievances.db')
    return conn

def create_tables():
    conn = connect_database()
    cursor = conn.cursor()
    # Create grievances table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grievances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            complaint TEXT NOT NULL,
            ticketnumber TEXT NOT NULL,
            status TEXT NOT NULL,
            keywords TEXT NOT NULL
        )
    ''')
    # Create replies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            response TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def extractKeywords(complaint):
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(complaint)
    keywords = [word for word in word_tokens if word.isalnum() and word.lower() not in stop_words]
    return ' '.join(keywords)

def ticketNumberGenerator():
    while True:
        ticketNumber = random.randint(100000, 999999)
        if ticketNumber not in ticket_numbers:
            ticket_numbers.append(ticketNumber)
            return ticketNumber

def get_response_for_keywords(keywords):
    conn = connect_database()
    cursor = conn.cursor()
    response = ""
    for keyword in keywords.split():
        cursor.execute("SELECT response FROM replies WHERE keyword = ?", (keyword,))
        result = cursor.fetchone()
        if result:
            response = result[0]
            break
    conn.close()
    return response

@app.route("/R", methods=['POST'])
def handle():
    conn = connect_database()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM grievances")
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/C", methods=['POST'])
def add_grievance():
    data = request.get_json()
    name = data.get('name')
    complaint = data.get('complaint')
    ticketnumber = ticketNumberGenerator()
    status = 'pending'  # Set status to pending when a grievance is added
    keywords = extractKeywords(complaint)

    response = get_response_for_keywords(keywords)

    conn = connect_database()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO grievances (name, complaint, ticketnumber, status, keywords) VALUES (?, ?, ?, ?, ?)", 
                   (name, complaint, ticketnumber, status, keywords))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Grievance added successfully!", "ticketnumber": ticketnumber, "response": response}), 201

@app.route("/U", methods=['POST'])
def update_status():
    if not ticket_numbers:
        return jsonify({"message": "No grievances found!"}), 400

    ticketnumber = ticket_numbers.pop()  # Take the last element of the list
    status = 'closed'  # Set status to closed

    conn = connect_database()
    cursor = conn.cursor()
    cursor.execute("UPDATE grievances SET status = ? WHERE ticketnumber = ?", (status, ticketnumber))
    conn.commit()
    conn.close()

    return jsonify({"message": "Grievance status updated to closed!", "ticketnumber": ticketnumber}), 200

@app.route("/add_reply", methods=['POST'])
def add_reply():
    data = request.get_json()
    keyword = data.get('keyword')
    response = data.get('response')

    conn = connect_database()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO replies (keyword, response) VALUES (?, ?)", (keyword, response))
    conn.commit() 
    conn.close()
    
    return jsonify({"message": "Reply added successfully!"}), 201

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
