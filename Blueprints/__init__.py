from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import re
from pytz import timezone
from models import db
from models import User as Userlogger
import os
from flask import Flask


current_dir = os.path.abspath(os.path.dirname(__file__))
IST = timezone('Asia/Kolkata')
app = Flask(__name__)
instance_path = app.instance_path
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(current_dir,"instance/ticketshowdb.sqlite3")
app.config["SECRET_KEY"]=os.environ['signed_cookie']
db.init_app(app)
app.app_context().push()
bcrypt=Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
IST = timezone('Asia/Kolkata')
emailregex=("^[^\s@]+@[^\s@]+\.[^\s@]+$")
eregex=re.compile(emailregex)
passwordregex=("^(?=.*\\d)(?=.*[a-z])(?=.*[A-Z]).{8,}$")
pregex=re.compile(passwordregex)

@login_manager.user_loader
def load_user(user_id):
    return Userlogger.query.get(int(user_id))