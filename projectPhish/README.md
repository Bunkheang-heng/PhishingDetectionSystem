# Email Classification and Phishing Detection System

This project is a comprehensive email management and security application designed to fetch, classify, and detect phishing emails or spam. Built using Flask and integrated with Google Cloud's powerful machine learning capabilities, the application provides a robust solution for users to manage their inboxes more securely and efficiently.

## Key Features
- **Email Fetching**: Securely connect to email servers using IMAP and retrieve the latest emails from the user's inbox.
- **Machine Learning Integration**: Utilize a trained machine learning model hosted on Google Cloud AI Platform to classify emails in real-time.
- **Real-time Email Classification**: Identify potential phishing attempts and spam based on email content.
- **User-friendly Interface**: A simple, intuitive web interface built with Flask and Bootstrap to display email details, including sender information, subject, and categorized email body content.

## Technical Stack
- **Flask**: A lightweight WSGI web application framework in Python, used for building the web interface and handling HTTP requests.
- **Google Cloud AI Platform**: A robust platform for training, deploying, and managing machine learning models.
- **IMAP**: Internet Message Access Protocol for fetching emails from the server.
- **Scikit-learn**: A machine learning library in Python, used for training the email classification model.
- **Joblib**: Used for model serialization and deserialization.
- **HTML, CSS, Bootstrap**: For designing the web interface and ensuring responsiveness.

## Installation

### Prerequisites
- Python 3.6+
- Google Cloud SDK
- Git

### Clone the Repository
```bash
git clone https://github.com/Bunkheang-heng/PhishingDetection.git
cd PhishingDetection

**
Create a Virtual Environment**
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
