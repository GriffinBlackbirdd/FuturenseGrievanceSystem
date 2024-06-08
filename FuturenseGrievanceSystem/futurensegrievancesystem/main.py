from flask import Flask, request, jsonify
import sqlite3
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download('stopwords')
nltk.download('punkt')

app = Flask(__name__)

def connect_database():
    conn = sqlite3.connect('grievances.db')
    return conn

def create_table():
    conn = connect_database()
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()

def extractKeywords(complaint):
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(complaint)
    keywords = [word for word in word_tokens if word.isalnum() and word.lower() not in stop_words]
    return ' '.join(keywords)


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
    ticketnumber = data.get('ticketnumber')    
    status = data.get('status')
    keywords = extractKeywords(complaint)

    conn = connect_database()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO grievances (name, complaint, ticketnumber, status, keywords) VALUES (?, ?, ?, ?, ?)", 
                   (name, complaint, ticketnumber, status, keywords))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Grievance added successfully!"}), 201

if __name__ == "__main__":
    create_table()
    app.run(debug=True)