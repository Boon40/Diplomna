
from Decorators import check_confirmed
from Database import db_session, init_db
from Models import User

import uuid

from flask_login import LoginManager
from flask import Flask, request, render_template, redirect, make_response, url_for, session, flash, make_response, jsonify
from sqlalchemy.sql.expression import false
from sqlalchemy.sql.functions import user
from flask_login import login_user, login_required, current_user, logout_user
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import asc
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Mail, Message


login_manager = LoginManager()
app = Flask(__name__)
app.secret_key = "SECRET_KEY"
app.config.from_pyfile('Config.cfg')

s = URLSafeTimedSerializer('Secret!')
mail = Mail(app)

init_db()

login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(login_id=user_id).first()

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))

@app.route('/',methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        if current_user.confirmed == 1:
            return render_template("index.html")
        else:
            return redirect(url_for('unconfirmed'))
    else:
        return render_template("index_for_non_users.html")

def send_token(email):
    token = s.dumps(email, salt='email-confirm')
    msg = Message('Confirm Email', sender='diplomnatues@abv.bg', recipients=[email])
    link = url_for('confirm_email', token=token, _external=True)
    msg.body = 'Your link is {}'.format(link)
    mail.send(msg)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == "POST":
        firstName = request.form["firstName"]
        lastName = request.form["lastName"]
        password = request.form["password"]
        confirm_pasword = request.form["verify_password"]
        email = request.form["email"]

        user = User.query.filter_by(email=email).first()
        if(user is not None):
            flash("This email is already in use!", "danger")
            return render_template("register.html")

        if confirm_pasword == password:
            user = User(password=generate_password_hash(password), email=email, firstName=firstName, lastName=lastName, confirmed=True)

            #send_token(email)

            db_session.add(user)
            db_session.commit()

            user.login_id = str(uuid.uuid4())
            db_session.commit()
            login_user(user)
            flash('You registered and are now logged in. Welcome!', 'success')
            return redirect(url_for('unconfirmed'))
            #return render_template("go_confirm.html", email = email)
        else:
            flash("Passwords doesn`t match!","danger")

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'GET':
        return render_template("login.html")
    else:
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            flash("You are logged in!","success")
            user.login_id = str(uuid.uuid4())
            db_session.commit()
            login_user(user)
            return redirect(url_for('unconfirmed'))
        else:
            flash("Wrong email or password!","danger")
            return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    current_user.login_id = None
    db_session.commit()
    logout_user()
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
@check_confirmed
def profile():
    if request.method == "POST":
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()
        password = request.form["password"]
        if check_password_hash(current_user.password, request.form["password"]):
            if user is not None:
                flash("This email is already used!", "danger")
                return render_template("profile.html")
            current_user.email = email
            current_user.firstName = request.form["firstName"]
            current_user.lastName = request.form["lastName"]
            db_session.commit()
            flash("Profile Updated!", "success")
            return redirect(url_for('profile'))
        else:
            flash("Wrong password!", "danger")
            return redirect(url_for('profile'))
    else:
        return render_template("profile.html")

@app.route('/forgot_password', methods=["GET", "POST"])
def forgotPassword():
    if request.method == 'GET':
        return render_template("forgot_password.html")
    else:
        user = User.query.filter_by(email=request.form["email"]).first()
        subject = "Password reset requested"
        token = s.dumps(user.email, salt='recover-key')
        msg = Message(subject, sender='diplomnatues@abv.bg', recipients=[user.email])
        link = url_for('reset_with_token', token=token, _external=True)
        msg.body = 'Your link is {}'.format(link)
        mail.send(msg)
        return render_template('check_email.html')

@app.route('/resend', methods=['GET', 'POST'])
def resend():
    send_token(current_user.email)
    return redirect(url_for('unconfirmed'))

def send_token(email):
    token = s.dumps(email, salt='email-confirm')
    msg = Message('Confirm Email', sender='diplomnatues@abv.bg', recipients=[email])
    link = url_for('confirm_email', token=token, _external=True)
    msg.body = 'Your link is {}'.format(link)
    mail.send(msg)

@app.route('/reset/<token>', methods=["GET", "POST"])
def reset_with_token(token):
    try:
        email = s.loads(token, salt="recover-key", max_age=3600)
    except:
        flash('The link is invalid or has expired.', 'danger')
        return redirect(url_for('index'))

    user = User.query.filter_by(email=email).first()
    if request.method == 'POST':
        new_pass = request.form["new_pass"]
        new_pass_conf = request.form["conf_new_pass"]
        if new_pass == new_pass_conf:
            user.password = generate_password_hash(new_pass)
            db_session.add(user)
            db_session.commit()
    else:
        return render_template("recover_password.html")
    return redirect(url_for('login'))

@app.route('/confirm_email/<token>')
@login_required
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        email = s.loads(token, salt='email-confirm')
        user = User.query.filter_by(email=email).first() 
        db_session.delete(user)
        db_session.commit()
        flash('The confirmation link is invalid or has expired.', 'danger')
        return '<h1>The token is expired!</h1>'

    user = User.query.filter_by(email=email).first() 
    if user.confirmed:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.confirmed = True
        db_session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('index'))

@app.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect(url_for('index'))
    flash('Please confirm your account!', 'warning')
    return render_template('unconfirmed.html')

