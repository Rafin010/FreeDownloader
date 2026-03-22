from flask import Flask, render_template, request, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# এই রাউটটি প্রতিবার একটি করে ইমেইল রিসিভ করবে এবং সেন্ড করবে
@app.route('/send-single', methods=['POST'])
def send_single():
    data = request.json
    sender_email = data.get('sender_email')
    sender_password = data.get('sender_password')
    recipient = data.get('recipient')
    subject = data.get('subject')
    message_body = data.get('message')

    if not all([sender_email, sender_password, recipient, subject, message_body]):
        return jsonify({"status": "error", "message": "সবগুলো তথ্য দেওয়া হয়নি!"}), 400

    try:
        # জিমেইলের SMTP সার্ভার সেটআপ
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        # লগিন করা (এখানে জিমেইলের App Password ব্যবহার করতে হবে)
        server.login(sender_email, sender_password)

        # ইমেইল তৈরি করা
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(message_body, 'plain'))

        # ইমেইল সেন্ড করা
        server.send_message(msg)
        server.quit()

        return jsonify({"status": "success", "email": recipient})
    except Exception as e:
        return jsonify({"status": "error", "email": recipient, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)