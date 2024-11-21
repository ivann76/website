import pickle
import joblib
import pandas as pd 
import sqlite3
import warnings
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, flash

warnings.filterwarnings('ignore')

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Load the stroke prediction model
model = joblib.load("stroke_model.pkl")

# Check the type of the loaded model
print("Loaded model type:", type(model))

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    # Relationship to StrokeInput
    stroke_inputs = db.relationship('StrokeInput', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'
    
class Contact(db.Model):
    __tablename__ = 'contact'
    id = db.Column(db.Integer, primary_key=True)
    contact = db.Column(db.String, nullable=False, unique=True)
    email = db.Column(db.String, nullable=False)
    message = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False, unique=True)

    def __repr__(self):
        return f'<Contact id={self.id} email={self.email}>' 

class StrokeInput(db.Model):
    __tablename__ = 'stroke_inputs'
    id = db.Column(db.Integer, primary_key=True)
    age = db.Column(db.Float, nullable=False)
    hypertension = db.Column(db.Boolean, nullable=False)
    heart_disease = db.Column(db.Boolean, nullable=False)
    avg_glucose = db.Column(db.Float, nullable=False)
    bmi = db.Column(db.Float, nullable=False)
    smoking_status = db.Column(db.String(50), nullable=False)
    marital_status = db.Column(db.String(50), nullable=False)
    work_type = db.Column(db.String(50), nullable=False)

    # Foreign key linking to the User table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<StrokeInput ID {self.id}, User {self.user_id}>'


# # Initialize the SQLite database
# def init_db():
#     conn = sqlite3.connect('users.db')
#     cursor = conn.cursor()
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             username TEXT UNIQUE NOT NULL,
#             password TEXT NOT NULL
#         )
#     ''')
#     conn.commit()
#     conn.close()

# Home page
@app.route('/')
def home():
    return render_template('home.html')

# Input page where users submit medical details
@app.route('/input', methods=['GET', 'POST'])
def input():
    if request.method == 'POST':
        # Retrieve form data (same as before)
        name = request.form.get('name')
        age = float(request.form.get('age'))
        gender = request.form.get('gender')

        # Convert hypertension and heart disease responses to numerical values
        hypertension_value = 1 if request.form.get('hypertension') == 'yes' else 0
        heart_disease_value = 1 if request.form.get('heart_disease') == 'yes' else 0

        # Retrieve other form data
        avg_glucose = float(request.form.get('avg_glucose'))
        bmi = float(request.form.get('bmi'))
        marital_status = request.form.get('marital_status')
        residence_type = request.form.get('residence_type')
        smoking_status = request.form.get('smoking_status')
        work_type = request.form.get('work_type')

        # Prepare input data for prediction
        input_data = [[age, hypertension_value, heart_disease_value, avg_glucose, bmi, smoking_status, marital_status, work_type]]
        columns = ['AGE', 'HYPERTENSION', 'HEART_DISEASE', 'AVG_GLUECOSE_LEVEL', 'BMI', 'SMOKING_STATUS', 'MARITAL_STATUS', 'WORK_TYPE']
        input_df = pd.DataFrame(input_data, columns=columns)

        # Print input data for debugging
        print("Input Data for Prediction:", input_data)

        # Predict using the model (get probability)
        try:
            # Use predict_proba to get the probability of stroke (class 1)
            prob = model.predict_proba(input_df)  # Returns probabilities for both classes
            stroke_probability = prob[0][1]  # The probability of stroke (class 1)
            stroke_percentage = stroke_probability * 100  # Convert to percentage
            stroke_prediction = 'Yes' if stroke_probability >= 0.5 else 'No'  # Threshold to decide stroke occurrence

        except Exception as e:
            print("Error during prediction:", e)
            stroke_prediction = f"Error in prediction: {e}"
            stroke_percentage = None  # In case of error, don't show percentage

        # Pass the collected data and prediction to the result page
        return render_template('result.html',
                               name=name,
                               age=age,
                               gender=gender,
                               hypertension=hypertension_value,
                               heart_disease=heart_disease_value,
                               avg_glucose=avg_glucose,
                               bmi=bmi,
                               marital_status=marital_status,
                               residence_type=residence_type,
                               smoking_status=smoking_status,
                               work_type=work_type,
                               stroke_prediction=stroke_prediction,
                               stroke_percentage=stroke_percentage)  # Add the percentage to the result page

    return render_template('input.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and user[0] == password:  # In a real app, use hashed passwords
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

# Signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        new_user = User(username=username, password=password)
        try:
            db.session.add(new_user)  # Add the user to the database session
            db.session.commit()  # Commit the transaction
            return "Signup successful!"
        except Exception as e:
            db.session.rollback()  # Rollback the transaction if there's an error
            return f"Error: {e}"

    return render_template('signup.html')

# About Us page
@app.route('/about')
def about():
    return render_template('about.html')

# Information page
@app.route('/info')
def info():
    return render_template('info.html')

# Contact Us page
@app.route('/contact', methods = ['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Retrieve data from the frontend
        name = request.form.get('name')
        message = request.form.get('message')
        email = request.form.get('email')

        add_contact = Contact(name=name, message=message, email=email)
        try:
            db.session.add(add_contact)  # Add the user to the database session
            db.session.commit()  # Commit the transaction
            return "add successful!"
        except Exception as e:
            db.session.rollback()  # Rollback the transaction if there's an error
            return f"Error: {e}"

    return render_template('contact.html')

# Run the Flask app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Creates all tables defined in your models

    app.run(debug=True)