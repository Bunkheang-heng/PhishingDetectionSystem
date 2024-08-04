from flask import Flask, render_template, request, url_for
from markupsafe import Markup
import imaplib
import email
from email.header import decode_header
import chardet
import logging
import joblib
import shap
import pandas as pd

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

# Load the trained machine learning model
model = joblib.load('model/email_classifier.pkl')

# Create a sample data frame for SHAP KernelExplainer
# This should be a small representative sample of the training data
df_sample = pd.DataFrame({
    'text': ["sample email text here"],  # Replace with actual sample text
    'label': [0]  # Replace with actual sample label
})

# Vectorize the sample text
vectorizer = model.named_steps['tfidfvectorizer']
X_sample = vectorizer.transform(df_sample['text'])

# Initialize SHAP KernelExplainer
explainer = shap.KernelExplainer(model.named_steps['multinomialnb'].predict_proba, X_sample)


def decode_subject(subject):
    decoded_bytes, encoding = decode_header(subject)[0]
    if isinstance(decoded_bytes, bytes):
        return decoded_bytes.decode(encoding or 'utf-8')
    return decoded_bytes


def decode_body(body):
    try:
        return body.decode('utf-8')
    except UnicodeDecodeError:
        encoding = chardet.detect(body)['encoding']
        return body.decode(encoding)


def fetch_emails(username, app_password, imap_server, mailbox='INBOX', num_emails=10):
    emails = []
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(username, app_password)
        mail.select(mailbox)
        status, messages = mail.search(None, 'ALL')
        email_ids = messages[0].split()

        logging.debug(f"Found {len(email_ids)} emails")

        latest_email_ids = email_ids[-num_emails:]

        for email_id in reversed(latest_email_ids):
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = decode_subject(msg['Subject'])
                    from_ = decode_subject(msg.get('From'))
                    date = msg['Date']
                    email_content = {
                        "id": email_id.decode(),
                        "subject": subject,
                        "from": from_,
                        "body": "",
                        "date": date
                    }
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            try:
                                body = part.get_payload(decode=True)
                                if body:
                                    email_content["body"] += decode_body(body)
                            except Exception as e:
                                logging.error(f"Error decoding part: {e}")
                    else:
                        content_type = msg.get_content_type()
                        body = msg.get_payload(decode=True)
                        if body:
                            email_content["body"] = decode_body(body)

                    # Get the phishing probability and classification
                    phishing_proba, classification = classify_email(email_content['body'])

                    email_content['phishing_probability'] = phishing_proba
                    email_content['classification'] = classification
                    email_content["snippet"] = email_content["body"][:100] + '...' if len(email_content["body"]) > 100 else email_content["body"]
                    emails.append(email_content)
        mail.close()
        mail.logout()
    except imaplib.IMAP4.error as e:
        logging.error(f"IMAP error: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

    return emails


def classify_email(text):
    proba = model.predict_proba([text])[0]
    phishing_proba = round(proba[1] * 100)  # Round to the nearest whole number

    # Determine classification based on phishing probability
    if phishing_proba <= 40:
        classification = "safe"
    elif 40 < phishing_proba <= 70:
        classification = "suspicious"
    else:
        classification = "phishing"

    return phishing_proba, classification

def highlight_phishing_areas(text):
    # Vectorize the text
    vectorized_text = vectorizer.transform([text])
    
    # Use SHAP to explain the prediction
    shap_values = explainer.shap_values(vectorized_text, nsamples=100)
    
    # Get the SHAP values for the words
    words = text.split()
    shap_values_for_text = shap_values[1][0]  # Assuming '1' is the label for phishing
    
    # Highlight words with high SHAP values
    highlighted_text = ""
    for i, word in enumerate(words):
        if i < len(shap_values_for_text) and shap_values_for_text[i] > 0:
            highlighted_text += f'<mark>{word}</mark> '
        else:
            highlighted_text += word + ' '
    
    return highlighted_text


def fetch_email_by_id(username, app_password, imap_server, email_id, mailbox='INBOX'):
    email_content = {}
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(username, app_password)
        mail.select(mailbox)
        status, msg_data = mail.fetch(email_id, '(RFC822)')
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject = decode_subject(msg['Subject'])
                from_ = decode_subject(msg.get('From'))
                date = msg['Date']
                email_content = {
                    "subject": subject,
                    "from": from_,
                    "body": "",
                    "date": date
                }
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        try:
                            body = part.get_payload(decode=True)
                            if body:
                                email_content["body"] += decode_body(body)
                        except Exception as e:
                            logging.error(f"Error decoding part: {e}")
                else:
                    content_type = msg.get_content_type()
                    body = msg.get_payload(decode=True)
                    if body:
                        email_content["body"] = decode_body(body)
                email_content['phishing_probability'] = classify_email(email_content['body'])
                email_content['body'] = Markup(highlight_phishing_areas(email_content['body']))
        mail.close()
        mail.logout()
    except imaplib.IMAP4.error as e:
        logging.error(f"IMAP error: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

    return email_content


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/fetch-emails', methods=['GET', 'POST'])

@app.route('/fetch-emails', methods=['GET','POST'])

def fetch_emails_route():
    username = request.form.get('username')
    app_password = request.form.get('app_password')
    imap_server = request.form.get('imap_server')

    logging.debug(f"Fetching emails for user: {username} with server: {imap_server}")

    emails = fetch_emails(username, app_password, imap_server)
    logging.debug(f"Fetched {len(emails)} emails")
    for email in emails:
        print(email)
    return render_template('emails.html', emails=emails, username=username, app_password=app_password, imap_server=imap_server)


@app.route('/email/<email_id>')
def email_detail(email_id):
    username = request.args.get('username')
    app_password = request.args.get('app_password')
    imap_server = request.args.get('imap_server')

    if not username or not app_password or not imap_server:
        logging.error("Missing parameters for fetching email details.")
        return "Missing parameters", 400

    email_content = fetch_email_by_id(username, app_password, imap_server, email_id)
    return render_template('email_detail.html', email=email_content)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about_us.html')


if __name__ == '__main__':
    app.run(host='localhost', port=5002, debug=True)
