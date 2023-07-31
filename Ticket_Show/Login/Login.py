from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from flask_login import login_user, logout_user, current_user, login_required
import re
from models import db, User
from .. import bcrypt, eregex, pregex
login_bp = Blueprint('login', __name__, template_folder='../templates', static_folder='../static')

@login_bp.route('/logout')
@login_required
def logout():
  session['rating']="None"
  session['date'] = ""
  session['location']="None"
  session['tags']="None"
  logout_user()
  flash("Succesfully logged out","success")
  return redirect(url_for('login.login',signup='login'))

@login_bp.route("/User/<string:signup>", methods=['GET', 'POST'])
def login(signup):
  if request.method == 'POST':
    if request.form.get('request_type') == "login":
      Email = (request.form.get('Email')).lower()
      Password = request.form.get('Password')
      if Email != None:
        if re.search(eregex,Email):
          if re.search(pregex,Password):
            user=User.query.filter_by(email = Email).first()
            if user:
              if bcrypt.check_password_hash(user.password,Password):
                if user.level=='b':
                  login_user(user)
                  flash('Successfully logged in!', 'success')
                  return redirect(url_for('user.Dashboard'))
                else:
                  flash("You are an admin, use this login page.",'danger')
                  return redirect(url_for('login.Adminlogin',signup='login'))#render_template('Adminlogin.html',signup='login')
              else:
                flash("Incorrect password.",'danger')
                return render_template('login.html',signup='login')
            else:
              flash("User does not exist, please sign up.",'danger')
              return render_template('login.html',signup='signup')
          else:
            flash("Passwords do not meet standards.",'danger')
            return render_template('login.html',signup='login')
        else:
          flash("Enter a valid email.",'danger')
          return render_template('login.html',signup='login')
      else:
        flash("Enter an email.",'danger')
        return render_template('login.html',signup='login')
    elif request.form.get("request_type") == "signup":
      Email = (request.form.get('Email')).lower()
      Password = request.form.get('Password')
      RePassword = request.form.get('RePassword')
      
      if Email != None:
        if re.search(eregex,Email):
          if not User.query.filter_by(email=Email).first():
            if re.search(pregex,Password):
              if Password == RePassword:
                password=bcrypt.generate_password_hash(Password)
                new_user=User(username = Email[:(Email.index("@"))], email = Email, password = password, level = "b")
                db.session.add(new_user)
                db.session.commit()
                curr_user = User.query.filter_by(email=Email).first()
                login_user(curr_user)
                flash("Successfully logged in!","success")
                return redirect(url_for('user.Dashboard'))
              else:
                flash("Passwords do not match.","danger")
                return render_template('login.html',signup='signup')
            else:
              flash("Password does not meet the requirements.","danger")
              return render_template('login.html',signup='signup')
          else:
            flash("Account already exists.","danger")
            return render_template('login.html',signup='login')
        else:
          flash("Email should resemble example@xyz.com.","danger")
          return render_template('login.html',signup='signup')
      else:
        flash("Email should not be left blank.","danger")
        return render_template('login.html',signup='signup')
    flash("Please try again later.","danger")
    return render_template('login.html',signup='signup')
  elif request.method == 'GET':
    if current_user.is_authenticated:
      if current_user.level=='b':
        return redirect(url_for("user.Dashboard"))
      elif current_user.level=='a':
        return redirect(url_for("admin.Dashboard"))
    else:
      return render_template('login.html', signup = signup)

@login_bp.route("/Admin/<string:signup>", methods=['GET', 'POST'])
def Adminlogin(signup):
  if request.method == 'POST':
    if request.form.get('request_type') == "login":
      Email = (request.form.get('Email')).lower()
      Password = request.form.get('Password')
      if Email != None:
        if re.search(eregex,Email):
          if re.search(pregex,Password):
            user=User.query.filter_by(email = Email).first()
            if user:
              if bcrypt.check_password_hash(user.password,Password):
                if user.level=='a':
                  login_user(user)
                  flash('Successfully logged in!', 'success')
                  return redirect(url_for('admin.Dashboard'))
                else:
                  flash("You are not an admin, login as a user.",'danger')
                  return redirect(url_for('login.login',signup='login'))#render_template('login.html',signup='login')
              else:
                flash("Incorrect password.",'danger')
                return render_template('Adminlogin.html',signup='login')
            else:
              flash("User does not exist, please sign up.",'danger')
              return render_template('Adminlogin.html',signup='signup')
          else:
            flash("Passwords do not meet standards.",'danger')
            return render_template('Adminlogin.html',signup='login')
        else:
          flash("Enter a valid email.",'danger')
          return render_template('Adminlogin.html',signup='login')
      else:
        flash("Enter an email.",'danger')
        return render_template('Adminlogin.html',signup='login')
    elif request.form.get("request_type") == "signup":
      Email = (request.form.get('Email')).lower()
      Password = request.form.get('Password')
      RePassword = request.form.get('RePassword')
      
      if Email != None:
        if re.search(eregex,Email):
          if not User.query.filter_by(email=Email).first():
            if re.search(pregex,Password):
              if Password == RePassword:
                password=bcrypt.generate_password_hash(Password)
                new_user=User(username = Email[:(Email.index("@"))], email = Email, password = password, level = "a")
                db.session.add(new_user)
                db.session.commit()
                curr_user = User.query.filter_by(email=Email).first()
                login_user(curr_user)
                flash("Successfully logged in!","success")
                return redirect(url_for('admin.Dashboard'))
              else:
                flash("Passwords do not match.","danger")
                return render_template('Adminlogin.html',signup='signup')
            else:
              flash("Password does not meet the requirements.","danger")
              return render_template('Adminlogin.html',signup='signup')
          else:
            flash("Account already exists.","danger")
            return render_template('Adminlogin.html',signup='login')
        else:
          flash("Email should resemble example@xyz.com.","danger")
          return render_template('Adminlogin.html',signup='signup')
      else:
        flash("Email should not be left blank.","danger")
        return render_template('Adminlogin.html',signup='signup')
    flash("Please try again later.","danger")
    return render_template('login.html',signup='signup')
  elif request.method == 'GET':
    if current_user.is_authenticated:
      if user.level=='b':
        return redirect(url_for("user.Dashboard"))
      elif user.level=='a':
        return redirect(url_for("user.Dashboard"))

    else:
      return render_template('Adminlogin.html', signup = signup)


