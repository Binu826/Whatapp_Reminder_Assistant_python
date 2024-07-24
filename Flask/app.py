import bcrypt
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm
import pyautogui
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from flask_mysqldb import MySQL
from wtforms.validators import DataRequired
import mysql.connector
import pymysql
from flask_mail import Mail, Message
import pywhatkit
import datetime
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time


app = Flask(__name__)



app.config['MAIL_SERVER'] = 'smtp.outlook.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'agneljosy1@outlook.com'
app.config['MAIL_PASSWORD'] = 'Agnel@1234'

mysql = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='mydatabase'
)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Update with your MySQL password
app.config['MYSQL_DB'] = 'mydatabase'
app.secret_key = 'your_secret_key'  # Update with your secret key

mysql = MySQL(app)

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    country_code = StringField("Country Code", validators=[DataRequired(), Length(min=1, max=4)])
    phone_number = StringField("Phone Number", validators=[DataRequired(), Length(min=10, max=15)])
    company_name = StringField("Company Name", validators=[DataRequired()])
    company_type = StringField("Company Type", validators=[DataRequired()])
    address = StringField("Address", validators=[DataRequired()])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password",validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password",validators=[DataRequired()])
    submit = SubmitField('Reset Password')


@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data.encode('utf-8')

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM user WHERE email = %s", [email])
        user = cursor.fetchone()
        cursor.close()

        if user and bcrypt.checkpw(password, user[3].encode('utf-8')):  # user[3] is the password field in the database
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            #flash('Login successful!', 'success')
            return redirect(url_for('contacts'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html', form=form)


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))

    return f"Welcome, {session['user_name']}!"


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data
        country_code = form.country_code.data
        phone_number = form.phone_number.data
        company_name = form.company_name.data
        company_type = form.company_type.data
        address = form.address.data

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO user (name, email, password, countrycode, phonenumber, companyname, companytype, address) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (name, email, hashed_password, country_code, phone_number, company_name, company_type, address)
        )
        mysql.connection.commit()
        
        cursor.execute("SELECT id FROM user WHERE name = %s", (name,))
        user_id = cursor.fetchone()[0]
        create_contact_table_for_user(user_id)
        cursor.close()

        #send_welcome_email(email, name)
        #flash('Signup successful! A welcome email has been sent to your email address.')
        return redirect(url_for('login'))
    return render_template('signin.html', form=form)

def create_contact_table_for_user(user_id):
    table_name = f'contacts_user_{user_id}'
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            contact_id INT(100) AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            country_code VARCHAR(10) NOT NULL,
            phone_number VARCHAR(20) NOT NULL,
            message TEXT)
            """)
    conn.commit()
    cursor.close()
    
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))



# # Route for the email template (optional)
# def send_welcome_email(email, name):
#     # Render HTML content for the email
#     html_content = render_template('email_template.html', name=name)
    
#     msg = Message(
#         subject="Welcome to WhatsApp Reminder Assistant!",
#         recipients=[email],
#         html=html_content
#     )
#     try:
#         msg.send()
#         print("[*] Email sent successfully! Please check your email.")
#     except Exception as e:
#         print(f"[*] Error sending email: {e}")

 
def send_welcome_email(request):
    From_email = 'agneljosy1@outlook.com'
    To_email = 'binuchiyyaram21@gmail.com'

 
    # Create a MIME multipart message
    msg = EmailMultiAlternatives(
        subject="Welcome to WhatsApp Reminder Assistant!",
        from_email=From_email,
        to=[To_email],
    )
    msg.attach_alternative('email_template.html', "text/html")
 
    try:
        msg.send()
        return HttpResponse("[*] Email sent successfully!")
    except Exception as e:
        return HttpResponse(f"[*] Error sending email: {e}")

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        current_password = form.current_password.data
        new_password = form.new_password.data
        user_id = session.get('user_id')  # Retrieve user_id from session

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(current_password.encode('utf-8'), user[3].encode('utf-8')):
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("UPDATE user SET password = %s WHERE id = %s", (hashed_password, user_id))
            mysql.connection.commit()
            cursor.close()
            flash('Password updated successfully!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Current password is incorrect.', 'danger')
    return render_template('forgot_password.html', form=form)

#############contacts page##############
# # Route for displaying contacts for each user that create table dynamicaly
@app.route('/contacts')
def contacts():
    if 'user_id' in session:
        try:
            user_id = int(session['user_id'])
        except ValueError:
            return "Invalid user ID", 400
        
        table_name = f'contacts_user_{user_id}'
        cur = mysql.connection.cursor()
        
        # Use string formatting to create the query dynamically
        query = f"SELECT contact_id , name, country_code, phone_number FROM {table_name}"
        
        cur.execute(query)
        contacts = cur.fetchall()
        cur.close()
        
        return render_template('contacts.html', contacts=contacts)
    return redirect(url_for('login'))
 
@app.route('/add_contact', methods=['GET', 'POST'])
def add_contact():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        country_code = request.form['country_code']
        phone_number = request.form['phone_number']
        user_id = session['user_id']

        table_name = f'contacts_user_{user_id}'
        cur = mysql.connection.cursor()

        # Insert contact details
        cur.execute(f"INSERT INTO {table_name} (name, country_code, phone_number) VALUES (%s, %s, %s)",
                    (name, country_code, phone_number))


        mysql.connection.commit()
        cur.close()

        return redirect(url_for('contacts'))
    return render_template('add_contacts.html')
    

@app.route('/delete_contact/<int:contact_id>', methods=['POST'])
def delete_contact(contact_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        user_id = int(session['user_id'])
    except ValueError:
        return "Invalid user ID", 400

    table_name = f'contacts_user_{user_id}'
    cur = mysql.connection.cursor()
    
    # Delete the contact from the dynamically created table
    query = f"DELETE FROM {table_name} WHERE contact_id = %s"
    
    cur.execute(query, (contact_id,))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('contacts'))


 
 
######main page######
@app.route('/mainpage')
def mainpage():
    final_message = request.args.get('final_message', '')
    return render_template('message_template.html', final_message=final_message)

@app.route('/message_template', methods=['GET', 'POST'])
def message_template():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = int(session['user_id'])

    if request.method == 'POST':
        try:
            message = request.form['Finalmessage']

            cur = mysql.connection.cursor()
            table_name = f'contacts_user_{user_id}'
            
            # Fetch all contact IDs
            cur.execute(f"SELECT contact_id FROM {table_name}")
            contact_ids = cur.fetchall()  # This will be a list of tuples

            # Iterate over each contact ID and update the message
            for contact in contact_ids:
                contact_id = contact[0]
                query = f"UPDATE {table_name} SET message = %s WHERE contact_id = %s"
                cur.execute(query, (message, contact_id))
            
            mysql.connection.commit()
            cur.close()
            
            session['template'] = message  # Store the template in the session for later use

            # Redirect to the generate_message endpoint for the first contact ID (or any contact ID you choose)
            return redirect(url_for('process_all_messages'))
        
        except KeyError as e:
            return f"Missing form field: {str(e)}", 400
        except Exception as e:
            return f"An error occurred: {str(e)}", 500

    # Retrieve contact IDs dynamically for the form
    cur = mysql.connection.cursor()
    table_name = f'contacts_user_{user_id}'
    cur.execute(f"SELECT contact_id, name FROM {table_name}")
    contacts = cur.fetchall()
    cur.close()

    return render_template('message_template.html', contacts=contacts)

@app.route('/process_all_messages')
def process_all_messages():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = int(session['user_id'])
    cur = mysql.connection.cursor()
    table_name = f'contacts_user_{user_id}'
    
    # Fetch all contact IDs
    cur.execute(f"SELECT contact_id FROM {table_name}")
    contact_ids = cur.fetchall()
    cur.close()

    return render_template('process_all_messages.html', contact_ids=contact_ids)


@app.route('/generate_message/<int:contact_id>', methods=['GET', 'POST'])
def generate_message(contact_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        user_id = int(session['user_id'])
    except ValueError:
        return "Invalid user ID", 400

    contact_table_name = f'contacts_user_{user_id}'
    cur = mysql.connection.cursor()

    # Fetch user details from the database
    cur.execute(f"SELECT name FROM {contact_table_name} WHERE contact_id = %s", (contact_id,))

    contact_details = cur.fetchone()

    if not contact_details:
        cur.close()
        return "Contact details not found", 404

    name = contact_details[0]

    # Get the template from the session
    template = session.get('template', '')

    # Generate the final message
    final_message = template.format(Name=name)

    # Update the final message in the database
    cur.execute(f"UPDATE {contact_table_name} SET message = %s WHERE contact_id = %s", (final_message, contact_id))
    mysql.connection.commit()
    cur.close()

    if request.method == 'POST':
        phone_number = request.form['phone_number']
        response = send_whatsapp_message_instantly(phone_number, final_message)
        return jsonify({'status': response})

    return render_template('message_template.html', final_message=final_message)


#######whatsapp msg send code##########
def send_whatsapp_message_instantly(phone_number, message):
    now = datetime.datetime.now()
    minute = now.minute + 2  # Send the message 2 minutes from now

    # Adjust minute and hour if minute goes beyond 59
    hour = now.hour
    if minute >= 60:
        minute -= 60
        hour += 1
        if hour >= 24:
            hour = 0

    try:
        pywhatkit.sendwhatmsg(phone_number, message, hour, minute)
        time.sleep(10)  # Wait for WhatsApp web to load and send the message
        pyautogui.hotkey('ctrl', 'w')  # Close the WhatsApp window
        return f"Message scheduled to be sent to {phone_number} at {hour:02d}:{minute:02d}"
    except Exception as e:
        return f"An error occurred: {e}"
    
@app.route('/send_message')
def send_message():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    table_name = f'contacts_user_{user_id}'

    # Fetch all contacts' phone numbers and messages
    cur.execute(f"SELECT phone_number, message FROM {table_name}")
    contacts = cur.fetchall()
    cur.close()

    responses = []
    for contact in contacts:
        phone_number, message = contact
        if not phone_number.startswith('+'):
            # Append your default country code if missing
            phone_number = f'+91{phone_number}'
            
        response = send_whatsapp_message_instantly(phone_number, message)
        responses.append(response)

    return jsonify({'status': 'messages scheduled', 'responses': responses})

# Route for displaying user profile
@app.route('/profile')
def profile():
    if 'user_id' in session:
        try:
            id = int(session['user_id'])
        except ValueError:
            return "Invalid user ID", 400
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT name, email, phonenumber, companyname, companytype, address FROM user WHERE id = %s", (id,))
        mem = cursor.fetchone()  # Use fetchone() to get a single user record
        
        cursor.close()
        
        if mem:
            return render_template('profile.html', mem=mem)
        else:
            return "User not found", 404
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
