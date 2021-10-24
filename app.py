from flask import Flask, render_template, request
from flask_wtf import FlaskForm, RecaptchaField, CSRFProtect
from wtforms import validators
from wtforms.fields.html5 import EmailField
from wtforms.fields import SelectField, SubmitField
from tinydb import TinyDB, Query
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
csrf = CSRFProtect(app)
app.secret_key = os.environ['SECRET_KEY']

db = TinyDB(os.environ["DATABASE_PATH"])
recipients = db.table("recipients")

class EmailForm(FlaskForm):
    email = EmailField("Email address", [validators.DataRequired(), validators.Email()])
    option = SelectField("Action", choices=[(0,"unsubscribe"), ('1','subscribe')])
    recaptcha = RecaptchaField()
    submit = SubmitField()

@app.route("/", methods=["GET", "POST"])
def home():
    form = EmailForm()
    if request.method == "POST":
        email_ = request.form.get("email")
        option_ = request.form.get("option")
        if option_ == "0":
            recipients.remove(Query().email == email_)
            return "Processed unsubscribe if email in database"
        if option_ == "1":
            print(email_, type(email_))
            for r in recipients:
                print(r)
            recipients.insert({"email":email_})
            return "Processed subscribe"
    return render_template('mgmt.html', form=form) 
