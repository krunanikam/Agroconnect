import smtplib
import random
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# SMTP Configuration (Use Google App Password, Not Regular Password)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "karunanikam379@gmail.com"  # Replace with your Gmail
EMAIL_PASSWORD = "evhdfkcctldxgzns"  # Replace with Google App Password

otp_storage = {}

# Database Setup
def init_db():
    conn = sqlite3.connect("farmer.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            commodity TEXT,
            quantity INTEGER,
            price REAL,
            address TEXT,
            mobile TEXT,
            email TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def send_email(to_email, otp):
    """ Sends an OTP via email and logs errors """
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        message = f"Subject: Your OTP Code\n\nYour OTP is: {otp}"
        server.sendmail(EMAIL_ADDRESS, to_email, message)
        server.quit()
        print(f"OTP {otp} sent to {to_email}")
        return True
    except smtplib.SMTPException as e:
        print(f"SMTP Error: {e}")
    return False

@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({"success": False, "message": "Email is required"}), 400

    otp = str(random.randint(100000, 999999))
    otp_storage[email] = otp

    if send_email(email, otp):
        return jsonify({"success": True, "message": "OTP sent successfully"})
    else:
        return jsonify({"success": False, "message": "Failed to send OTP"}), 500

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = data.get("email")
    otp = data.get("otp")

    if not email or not otp:
        return jsonify({"success": False, "message": "Email and OTP are required"}), 400

    if otp_storage.get(email) == otp:
        del otp_storage[email]  # Remove OTP after verification
        return jsonify({"success": True, "message": "OTP verified"})
    else:
        return jsonify({"success": False, "message": "Invalid OTP"}), 400

@app.route('/store-commodity', methods=['POST'])
def store_commodity():
    data = request.json
    name = data.get("farmerName")
    commodity = data.get("commodity")
    quantity = data.get("quantity")
    price = data.get("price")
    address = data.get("address")
    mobile = data.get("phone")
    email = data.get("email")

    if not all([name, commodity, quantity, price, address, mobile, email]):
        return jsonify({"success": False, "message": "All fields are required"}), 400

    try:
        quantity = int(quantity)
        price = float(price)
    except ValueError:
        return jsonify({"success": False, "message": "Invalid quantity or price"}), 400

    try:
        conn = sqlite3.connect("farmer.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO farmers (name, commodity, quantity, price, address, mobile, email) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, commodity, quantity, price, address, mobile, email))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Data stored successfully", "id": cursor.lastrowid})
    except sqlite3.Error as e:
        return jsonify({"success": False, "message": f"Database error: {e}"}), 500

@app.route('/get-farmers', methods=['GET'])
def get_farmers():
    try:
        conn = sqlite3.connect("farmer.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM farmers")
        farmers = cursor.fetchall()
        conn.close()

        farmer_list = [{"id": row[0], "name": row[1], "commodity": row[2], "quantity": row[3], "price": row[4], "address": row[5], "mobile": row[6], "email": row[7]} for row in farmers]
        return jsonify(farmer_list)
    except sqlite3.Error as e:
        return jsonify({"success": False, "message": f"Database error: {e}"}), 500

@app.route('/verify-email-for-deletion', methods=['POST'])
def verify_email_for_deletion():
    data = request.json
    id = data.get("id")
    email = data.get("email")

    if not id or not email:
        return jsonify({"success": False, "message": "ID and email are required"}), 400

    try:
        conn = sqlite3.connect("farmer.db")
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM farmers WHERE id = ?", (id,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            return jsonify({"success": False, "message": "Record not found"}), 404

        stored_email = result[0].strip().lower()  # Trim and convert to lowercase
        if stored_email == email.strip().lower():  # Trim and convert to lowercase
            return jsonify({"success": True, "message": "Email verified"})
        else:
            return jsonify({"success": False, "message": "Email does not match"}), 400
    except sqlite3.Error as e:
        return jsonify({"success": False, "message": f"Database error: {e}"}), 500

@app.route('/delete-farmer/<int:id>', methods=['DELETE'])
def delete_farmer(id):
    try:
        conn = sqlite3.connect("farmer.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM farmers WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Entry deleted successfully"})
    except sqlite3.Error as e:
        return jsonify({"success": False, "message": f"Database error: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)