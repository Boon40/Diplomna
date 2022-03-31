from Database import db_session, init_db
from Models import Notification, User, Signal

from datetime import datetime
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

mail = Mail(app)

s = URLSafeTimedSerializer('Secret!')

init_db()
    
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(login_id=user_id).first()

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))

@app.route('/current_signals', methods=['GET', 'POST'])
def current_signals():
    if current_user.is_authenticated:
        data = Signal.query.all()
        signals = []
        for i in reversed(data):
            if not i.closed:
                signals.append(i)
        return render_template("current_signals.html", signals=enumerate(signals))
    else:
        return render_template("index_for_non_users.html")

@app.route('/closed_signals', methods=['GET', 'POST'])
def closed_signals():
    if current_user.is_authenticated:
        data = Signal.query.all()
        signals = []
        for i in reversed(data):
            if i.closed:
                signals.append(i)
        return render_template("closed_signals.html", signals=enumerate(signals))
    else:
        return render_template("index_for_non_users.html")

@app.route('/',methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        info = Notification.query.order_by(Notification.id.desc()).limit(20).all()
        data = Signal.query.all()
        signals = []
        notifications = []
        for i in info:
            notifications.append(i)
        for i in data:
            signals.append(i)
        return render_template("index.html", notifications=enumerate(notifications), signals=enumerate(signals))
    else:
        return render_template("index_for_non_users.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        firstName = request.form["firstName"]
        lastName = request.form["lastName"]
        password = request.form["password"]
        confirm_pasword = request.form["verify_password"]
        email = request.form["email"]
        dt = request.form["birth_date"]
        dt = datetime.strptime(dt, "%Y-%m-%d")
        date_of_birth = dt.date()

        user = User.query.filter_by(email=email).first()
        if(user is not None):
            flash("This email is already in use!", "danger")
            return render_template("register.html")
        
        if ((datetime.now().date() - date_of_birth).days / 365) < 18:
            flash("You need to be 18+ to register!", "danger")
            return render_template("register.html")

        if confirm_pasword == password:
            user = User(password=generate_password_hash(password), email=email, firstName=firstName, lastName=lastName, birthDate=date_of_birth)

            db_session.add(user)
            db_session.commit()

            user.login_id = str(uuid.uuid4())
            db_session.commit()
            login_user(user)
            flash('Register successful. You are now logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash("Passwords doesn`t match!","danger")

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    else:
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            flash("You are logged in!","success")
            user.login_id = str(uuid.uuid4())
            db_session.commit()
            login_user(user)
            return redirect(url_for('index'))
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

@app.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email():
    if request.method == "POST":
        currentEmail = request.form["currentEmail"]
        newEmail = request.form["newEmail"]
        confirmNewEmail = request.form["confirmNewEmail"]
        password = request.form["password"]
        if current_user.email == currentEmail:
            user = User.query.filter_by(email=newEmail).first()
            if user is not None:
                flash("This email is already used!", "danger")
                return render_template("change_email.html")
            if newEmail == confirmNewEmail:
                if check_password_hash(current_user.password, request.form["password"]):
                    current_user.email = newEmail
                    db_session.commit()
                    flash("Email updated!", "success")
                    return redirect (url_for('index'))
                else:
                    flash("Wrong password!", "danger")
                    return render_template("change_email.html")
            else:
                flash("Emails don't match!", "danger")
                return render_template("change_email.html")
        else:
            flash("The email you are trying to change is not yours!", "danger")
            return render_template("change_email.html")
    else:
        return render_template("change_email.html")

@app.route('/change_names', methods=['GET', 'POST'])
@login_required
def change_names():
    if request.method == "POST":
        newFirstName = request.form["newFirstName"]
        newLastName = request.form["newLastName"]
        password = request.form["password"]            
        if check_password_hash(current_user.password, request.form["password"]):
            current_user.firstName = newFirstName
            current_user.lastName = newLastName
            db_session.commit()
            flash("Names Updated!", "success")
            return redirect(url_for('index'))
        else:
            flash("Wrong password", "danger")
            return redirect(url_for('change_names'))
    else:
        return render_template("change_names.html")

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == "POST":
        currentPassword = request.form["currentPassword"]
        newPassword = request.form["newPassword"]
        confirmNewPassword = request.form["confirmNewPassword"]
        if check_password_hash(current_user.password, request.form["currentPassword"]):
            if newPassword == confirmNewPassword:
                current_user.password = generate_password_hash(newPassword)
                db_session.commit()
                flash("Password Updated!", "success")
                return redirect(url_for('index'))
            else:
                flash("Passwords does not match", "danger")
                redirect(url_for('change_password'))
        else:
            flash("Wrong password!", "danger")
            return redirect(url_for('change_password'))
    else:
        return render_template("change_password.html")

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

@app.route('/resend', methods=['GET', 'POST'])
def resend():
    send_token(current_user.email)
    return redirect(url_for('unconfirmed'))

def send_token(email):
    token = s.dumps(email, salt='email-confirm')
    msg = Message('Confirm Email', sender='nov_meil_tues@abv.bg', recipients=[email])
    link = url_for('confirm_email', token=token, _external=True)
    msg.body = 'Your link is {}'.format(link)
    mail.send(msg)

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
        return render_template('check_email.html')


