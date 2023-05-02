import os
from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, desc, update
from flask_bcrypt import Bcrypt
from flask_login import  UserMixin, LoginManager, login_user, logout_user, current_user, login_required
import plotly.graph_objects as go
import re
from datetime import datetime, time, timedelta
from pytz import timezone

current_dir = os.path.abspath(os.path.dirname(__file__))
IST = timezone('Asia/Kolkata')
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(current_dir,"ticketshowdb.sqlite3")
app.config["SECRET_KEY"]=os.environ['signed_cookie']
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()
bcrypt=Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
  
class User(db.Model, UserMixin):
  __tablename__ = 'user'
  user_id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
  username = db.Column(db.String, nullable=False)
  email = db.Column(db.String, unique=True, nullable=False)
  password = db.Column(db.String, nullable=False)
  level = db.Column(db.CHAR, nullable=False)
  def get_id(self):
    return (self.user_id)

class Admin(db.Model):
  __tablename__ = 'admin'
  stage_id = db.Column(db.Integer,autoincrement=True, primary_key=True, nullable=False)
  user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
  location = db.Column(db.String)
  stage = db.Column(db.String, nullable=False)
  seats = db.Column(db.Integer, nullable=False)

class Show(db.Model):
  __tablename__ = 'show'
  user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
  stage_id = db.Column(db.Integer, db.ForeignKey("admin.stage_id"), nullable=False)
  show_id = db.Column(db.Integer,autoincrement=True, primary_key=True, nullable=False)
  starttime = db.Column(db.DateTime(timezone=True), nullable=False)
  endtime = db.Column(db.DateTime(timezone=True), nullable=False)
  stage = db.Column(db.String, nullable=False)
  show = db.Column(db.String, nullable=False)
  seats_left = db.Column(db.Integer, nullable=False)
  cost = db.Column(db.Integer, nullable=False)
  tags = db.Column(db.String, nullable=True)



class Stats(db.Model):
  __tablename__ = 'stats'
  user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False, primary_key=True)
  best_stage = db.Column(db.String, nullable=False)
  time_fill_stage = db.Column(db.String, nullable=False)
  best_show = db.Column(db.String, nullable=False)
  time_fill_show = db.Column(db.String, nullable=False)
  average_timefill_stage = db.Column(db.String, nullable=False)
  average_timefill_show = db.Column(db.String, nullable=False)

class Rating(db.Model):
  __tablename__ = 'rating'
  show = db.Column(db.String, db.ForeignKey('show.show'), primary_key=True, nullable=False)
  rating = db.Column(db.Float, nullable=False)
  stars = db.Column(db.Integer, nullable=False)
  count = db.Column(db.Integer, nullable=False)

class Request(db.Model):
  __tablename__ = 'request'
  email = db.Column(db.String, db.ForeignKey("user.email"), nullable=False, primary_key=True)

class Bookings(db.Model):
  __tablename__ = 'bookings'
  booking_id = db.Column(db.Integer, nullable=False, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
  show_id = db.Column(db.Integer, db.ForeignKey("show.show_id"), nullable=False)
  show = db.Column(db.String, db.ForeignKey('show.show'), nullable=False)
  cost = db.Column(db.Integer, nullable=False)
  tickets = db.Column(db.Integer, nullable=False)
  rating = db.Column(db.Integer, nullable=False)  
    

emailregex=("^[^\s@]+@[^\s@]+\.[^\s@]+$")
eregex=re.compile(emailregex)
passwordregex=("^(?=.*\\d)(?=.*[a-z])(?=.*[A-Z]).{8,}$")
pregex=re.compile(passwordregex)

@app.route('/', methods=['GET', 'POST'])
def front_page():
  return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
  session['rating']="None"
  session['date'] = ""
  session['location']="None"
  session['tags']="None"
  logout_user()
  flash("Succesfully logged out","success")
  return redirect(url_for('login',signup='login'))

@app.route('/sellerpermissions')
@login_required
def sellerpermissions():
    flash("Seller permissions has been requested.",'danger')
    DoesNotExist = (db.session.query(Request).filter_by(email=current_user.email).first() is None)
    if DoesNotExist:
      req=Request(email=current_user.email)
      db.session.add(req)
      db.session.commit()
    return redirect(url_for('Dashboard'))

@app.route('/approval/<string:email>', methods=['GET', 'POST'])
@login_required
def approval(email):
    if current_user.email=="kewin.joshua@gmail.com":
      method = request.form.get('approval')
      if method=="REJECT":
        process_finished = db.session.query(Request).filter_by(email=email).first()
        flash(f"{user.email}'s request rejected.",'danger')
        db.session.delete(process_finished)
        db.session.commit()
      elif method=="ACCEPT":
        user = db.session.query(User).filter_by(email=email).first()
        flash(f"{user.email}'s request approved!",'success')
        user.level = 'a'
        db.session.commit()
        process_finished = db.session.query(Request).filter_by(email=email).first()
        db.session.delete(process_finished)
        db.session.commit()
    return redirect(url_for('Dashboard'))



@app.route("/entry/<string:signup>", methods=['GET', 'POST'])
def login(signup):
  if request.method == 'POST':
    if request.form.get('request_type') == "login":
      Email = (request.form.get('Email')).lower()
      Password = request.form.get('Password')
      if Email != None:
        if re.search(eregex,Email):
          if re.search(pregex,Password):
            user=User.query.filter_by(email = Email).filter(User.level=='b').first()
            if user:
              if bcrypt.check_password_hash(user.password,Password):
                login_user(user)
                flash('Successfully logged in!', 'success')
                return redirect(url_for('Dashboard'))
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
      return redirect(url_for('home'))
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
                return redirect(url_for('Dashboard'))
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
      return redirect(url_for("Dashboard"))
    else:
      return render_template('login.html', signup = signup)

@app.route("/Adminentry/<string:signup>", methods=['GET', 'POST'])
def Adminlogin(signup):
  if request.method == 'POST':
    if request.form.get('request_type') == "login":
      Email = (request.form.get('Email')).lower()
      Password = request.form.get('Password')
      if Email != None:
        if re.search(eregex,Email):
          if re.search(pregex,Password):
            user=User.query.filter_by(email = Email).filter(User.level=='a').first()
            if user:
              if bcrypt.check_password_hash(user.password,Password):
                login_user(user)
                flash('Successfully logged in!', 'success')
                return redirect(url_for('Dashboard'))
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
                return redirect(url_for('Dashboard'))
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
     return redirect(url_for("Dashboard"))
    else:
      return render_template('Adminlogin.html', signup = signup)


@app.route("/Dashboard", methods=['GET', 'POST'])
@login_required
def Dashboard():
  if request.method == 'GET':
    if current_user.email=="kewin.joshua@gmail.com":
      return render_template('admin_privilege.html', requesters=Request.query.all())
    if current_user.level=="b":
      events = db.session.query(Show, Rating.rating, Admin.location).join(Rating, Show.show == Rating.show, isouter=True).join(Admin, Show.stage_id == Admin.stage_id, isouter=True).filter(Show.endtime >= datetime.now(timezone('Asia/Kolkata'))).all()
      session['location']="None"
      session['rating']="None"
      session['date']=""
      session['tags']="None"
      return render_template('user_buyer.html', events=events, Locations = [locations.location for locations in Admin.query.distinct(Admin.location).all()])
    if current_user.level=="a":
      return render_template('user_seller.html',events=db.session.query(Show).filter_by(user_id=current_user.user_id).filter(Show.endtime >= datetime.now(timezone('Asia/Kolkata'))).all())
  elif request.method =='POST':
    rating=request.form.get('ratingfilter')
    location=request.form.get('locationfilter')
    date=request.form.get('datefilter')
    tags=request.form.get('tagsfilter')
    session['location']=location
    session['rating']=rating
    session['date']=date
    session['tags']=tags
    print(session['rating'],session['location'],session['date'])
    events = db.session.query(Show, Rating.rating, Admin.location).join(Rating, Show.show == Rating.show, isouter=True).join(Admin, Show.stage_id == Admin.stage_id, isouter=True).filter(Show.endtime >= datetime.now(timezone('Asia/Kolkata')))
    if rating:
      if rating!="None":
        events = events.filter(Rating.rating >= rating)
        print('runthorugh')
    if location:
      if location!="None":
        events = events.filter(Admin.location == location)
    if tags:
      if tags!="None":
        events = events.filter(Show.tags == tags)
    if date:
      date = datetime.strptime(date, '%Y-%m-%d')
      date = IST.localize(date)
      starter = datetime.combine(date, time.min)
      ender = datetime.combine(date, time.max)
      events = events.filter(((Show.starttime >= starter)&(Show.starttime <= ender))|((Show.endtime >= starter)&(Show.endtime <= ender)))
    events=events.all()
    return render_template('user_buyer.html', events=events, Locations = [locations.location for locations in Admin.query.distinct(Admin.location).all()])

@app.route('/delete_show/<int:show_id>', methods=['POST'])
@login_required
def delete_show(show_id):
    show = Show.query.get(show_id)
    if show is None:
      return redirect(url_for('Dashboard'))
    elif show.user_id!=current_user.user_id:
      return redirect(url_for('Dashboard'))
    else:
      db.session.delete(show)
      allbook=db.session.query(Bookings).filter_by(show_id=show_id).all()
      for book in allbook:
        db.session.delete(book)
      db.session.commit()
      flash(f'{show.show} deleted successfully!', 'success')
      return redirect(url_for('Dashboard'))

@app.route('/delete_venue/<int:stage_id>', methods=['POST'])
@login_required
def delete_venue(stage_id):
  stage = Admin.query.get(stage_id)
  if current_user.user_id==stage.user_id:
    if stage is None:
      return redirect(url_for('Dashboard'))
    elif stage.user_id!=current_user.user_id:
      flash('You do not own this stage', 'danger')
      return redirect(url_for('Dashboard'))
    shows=db.session.query(Show).filter_by(stage_id=stage_id).filter(Show.endtime>datetime.now()).all()
    if shows:
      flash('There are shows planned for this place, delete the shows before you delete the venue.', 'danger')
      return redirect(url_for('Dashboard'))
    else:
      flash(f'{stage.stage} deleted successfully!', 'success')
      db.session.delete(stage)
      db.session.commit()
      return redirect(url_for('editvenues'))
  else:
    return redirect(url_for('editvenues'))

@app.route('/edit_show/<int:show_id>', methods=['GET','POST'])
@login_required
def edit_show(show_id):
  show = Show.query.get(show_id)
  if current_user.user_id==show.user_id:
    if request.method == 'GET':
      show=Show.query.filter_by(show_id=show_id).first()
      return render_template('editshow.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id, location=(Admin.query.get(show.stage_id)).location), venue=show.stage_id, show=show.show, start=show.starttime, end=show.endtime, cost=show.cost, tag=show.tags)
    if request.method == 'POST':
      stage=request.form.get('Venue')
      show=request.form.get('Show')
      cost=int(request.form.get('cost'))
      tags=request.form.get('Genre')
      if not cost:
        flash('Please enter cost of ticket',"danger")
        return render_template('editshow.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id, location=(Admin.query.get(show.stage_id)).location), venue=show.stage_id, show=show.show, start=show.starttime, end=show.endtime, cost=show.cost, tag=show.tags)
      elif cost<0:
        flash('Cost should not be negative',"danger")
        return render_template('editshow.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id, location=(Admin.query.get(show.stage_id)).location), venue=show.stage_id, show=show.show, start=show.starttime, end=show.endtime, cost=show.cost, tag=show.tags)
      stage = int(stage)
      venue=db.session.query(Admin).filter_by(user_id=current_user.user_id).filter(Admin.stage_id==stage).first()
      if venue is not None:
        eshow=Show.query.filter_by(show_id=show_id).first()
        shower=((Admin.query.get(eshow.stage_id)).seats-venue.seats)
        if shower<eshow.seats_left:
          eshow.user_id=current_user.user_id
          eshow.stage_id=venue.stage_id
          eshow.stage=venue.stage
          eshow.cost=cost
          eshow.seats_left=eshow.seats_left-shower
          eshow.tags=tags
          db.session.commit()
          flash(f'{eshow.show} modified successfully!', 'success')
          return redirect(url_for('Dashboard'))
        else:
          flash('Booked tickets exceed the capacity for the new venue to accomodate.', 'danger')
          return render_template('editshow.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id, location=(Admin.query.get(show.stage_id)).location), venue=show.stage_id, show=show.show, start=show.starttime, end=show.endtime, cost=show.cost, tag=show.tags)
        
  else:
    return redirect(url_for('Dashboard'))
    
@app.route('/editvenue/<int:stage_id>', methods=['GET','POST'])
@login_required
def editvenue(stage_id):
  if request.method=='GET':
    venue=Admin.query.filter_by(stage_id=stage_id).filter(Admin.user_id==current_user.user_id).first()
    if venue:
      return render_template('editvenue.html',Stage=venue.stage,Seat=venue.seats,Location=venue.location)
    else:
      flash("You do not own this stage!",'danger')
      return redirect(url_for('Dashboard'))
  elif request.method=='POST':
    stage=request.form.get('Venue')
    seat=request.form.get('Capacity')
    if not stage:
      flash('Please enter venue name.',"danger")
      return render_template('editvenue.html')
    if not seat:
      flash('Please enter number of seats.',"danger")
      return render_template('editvenue.html')
    seat=int(seat)
    if seat<0:
      flash('Seats should not be negative.',"danger")
      return render_template('editvenue.html')
    venue=db.session.query(Admin).filter_by(stage_id=stage_id).filter(Admin.user_id==current_user.user_id).first()

    if venue:
      venue.stage=stage
      if venue.seats>seat:
        flash('Seats should not be lesser than current number of seats.',"danger")
        return render_template('newvenue.html')
      flash('Venue modified successfully',"success")
      update_stmt = db.session.query(Show).filter(Show.stage_id == venue.stage_id,Show.starttime > datetime.now()).update({"stage":venue.stage,"seats_left": Show.seats_left + (seat-venue.seats)})
      venue.seats=seat
      db.session.commit()
    return redirect(url_for('editvenues'))



@app.route('/editvenues', methods=['GET', 'POST'])
@login_required
def editvenues():
  return render_template('editvenues.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id).all())
  
@app.route('/newvenue', methods=['GET', 'POST'])
@login_required
def newvenue():
  if request.method=='GET':
    return render_template('newvenue.html')
  elif request.method=='POST':
    stage=request.form.get('Venue')
    seat=request.form.get('Capacity')
    location=request.form.get('Location')
    if not stage:
      flash('Please enter stage name.',"danger")
      return render_template('newvenue.html')
    if not seat:
      flash('Please enter number of seats.',"danger")
      return render_template('newvenue.html')
    if not location:
      flash('Please enter location.',"danger")
      return render_template('newvenue.html')
    seat=int(seat)
    if seat<0:
      flash('Seats should not be negative',"danger")
      return render_template('newvenue.html')
    venues=db.session.query(Admin).filter_by(user_id=current_user.user_id).filter(Admin.stage==stage).filter(Admin.seats==seat).filter(Admin.location==location).first()
    if venues is not None:
      flash('Venue already exists',"danger")
      return render_template('newvenue.html')
    else:
      seat=int(seat)
      new_venue=Admin(user_id=current_user.user_id,location=location,stage=stage,seats=seat)
      db.session.add(new_venue)
      db.session.commit()
      flash(f'{new_venue.stage} has been added successfully','success')
      return redirect(url_for('editvenues'))
    
@app.route("/newshow", methods=['GET', 'POST'])
@login_required
def newshow():
  if request.method == 'GET':
    return render_template('newshow.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id).all())
  if request.method == 'POST':
    stage=request.form.get('Venue')
    show=request.form.get('Show')
    start=request.form.get('start')
    start = datetime.strptime(start, '%Y-%m-%dT%H:%M')
    start = IST.localize(start)
    end=request.form.get('end')
    end = datetime.strptime(end, '%Y-%m-%dT%H:%M')
    end = IST.localize(end)
    cost=int(request.form.get('cost'))
    tags=request.form.get('Genre')
    genre=["Thriller","Romance","Comedy","Horror","Action","Drama"]
    if tags not in genre:
      flash('Invalid genre, please select a genre in the list',"danger")
      return render_template('newshow.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id).all())
    if start>end:
      flash('Start time should be before end time',"danger")
      return render_template('newshow.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id).all())
    if start<=datetime.now(timezone('Asia/Kolkata')) or end<=datetime.now(timezone('Asia/Kolkata')):
      flash('You cannot add shows to the past, we do not provide time machines.',"danger")
      return render_template('newshow.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id).all())
    if not cost:
        flash('Please enter cost of ticket',"danger")
        return render_template('newshow.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id).all())
    elif cost<0:
      flash('Cost should not be negative',"danger")
      return render_template('newshow.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id).all())
    stage = int(stage)
    venue=db.session.query(Admin).filter_by(user_id=current_user.user_id).filter(Admin.stage_id==stage).first()
    if venue is not None:
      new_show=Show(user_id=current_user.user_id, stage_id=venue.stage_id, starttime=start, endtime=end, stage=venue.stage, show=show, seats_left=venue.seats, cost=cost, tags=tags)
      clashing = db.session.query(Show).filter_by(user_id=current_user.user_id).filter(((Show.starttime <= start) & (Show.endtime >= start)) | ((Show.starttime <= end) & (Show.endtime >= end))).filter(Show.stage_id==stage).first()
      if clashing:
        err='New show timing clashes with '+clashing.show+' starting at '+(clashing.starttime).strftime("%m/%d/%Y, %H:%M:%S")+'.'
        flash(err,"danger")
        return render_template('newshow.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id).all())
      else:
        db.session.add(new_show)
        db.session.commit()
        flash(f'{new_show.show} has been added succesfully','success')
        return redirect(url_for('Dashboard'))

@app.route("/booktickets/<int:show_id>", methods=['GET', 'POST'])
@login_required
def book(show_id):
  if request.method == 'GET':
    show=Show.query.get(show_id)
    venue= Admin.query.get(show.stage_id)
    location=venue.location
    if IST.localize(show.endtime)> datetime.now(timezone('Asia/Kolkata')):
      return render_template('book.html',show=show,location=location)
    else:
      return redirect(url_for('Dashboard'))
  if request.method == 'POST':
    update=db.session.query(Show).filter_by(show_id=show_id).first()
    buying=int(request.form.get('bookingSeats'))
    new=update.seats_left-buying
    if buying==0:
      show=Show.query.get(show_id)
      venue= Admin.query.get(show.stage_id)
      location=venue.location
      if IST.localize(show.endtime)>datetime.now(timezone('Asia/Kolkata')):
        flash("You cannot book 0 tickets", 'danger')
        return render_template('book.html',show=show,location=location)
      else:
        flash("Show already ended or does not exist",'danger')
        return redirect(url_for('Dashboard'))
    if new<0:
      db.session.flush()
      flash('Sorry, the venue cannot accept that many guests.','danger')
      show=Show.query.get(show_id)
      venue= Admin.query.get(show.stage_id)
      location=venue.location
      if IST.localize(show.endtime)>datetime.now(timezone('Asia/Kolkata')):
        return render_template('book.html',show=show,location=location)
      else:
        flash("Show already ended or does not exist",'danger')
        return redirect(url_for('Dashboard'))
    else:
      update.seats_left=new
      show=Show.query.get(show_id)
      venue= Admin.query.get(show.stage_id)
      location=venue.location
      book=Bookings(user_id=current_user.user_id,show_id=show_id,show=show.show,cost=(show.cost)*(buying),tickets=buying,rating=0)
      db.session.add(book)
      db.session.commit()
      if buying>1:
        flash("Seats booked successfully",'success')
      elif buying>0:
        flash("Seat booked successfully",'success')
      return redirect(url_for('Dashboard'))

@app.route("/bookedtickets/", methods=['GET', 'POST'])
@login_required
def booked():
  if request.method == 'GET':
    events = db.session.query(Bookings, Show.starttime, Show.endtime, Admin.location, Show.stage).join(Show, Show.show_id == Bookings.show_id, isouter=True).join(Admin, Show.stage_id == Admin.stage_id, isouter=True).filter(Bookings.user_id==current_user.user_id).filter(Bookings.rating==0).all()
    eventsdt=[]
    for Booking,start,end,location,stage in events:
      start = IST.localize(start)
      end = IST.localize(end)
      eventsdt.append((Booking, start, end, location, stage))
    return render_template('booked.html',events=eventsdt,nowt = datetime.now(timezone('Asia/Kolkata')))

@app.route("/rating/<int:booking_id>", methods=['POST'])
@login_required
def rating(booking_id):
  if request.method == 'POST':
    eventer = db.session.query(Bookings).filter_by(booking_id=booking_id).first()
    events = db.session.query(Rating).filter_by(show=eventer.show).first()
    star = request.form.get('ratingfilter')
    if events:
      events.stars+=int(star)
      events.count+=1
      events.rating=events.stars/events.count
      eventer.rating=1
      db.session.commit()
    else:
      showr=Rating(show = eventer.show, rating = star, stars = star, count = 1 )
      db.session.add(showr)
      eventer.rating=1
      db.session.commit()
    flash(f'You have rated the show {eventer.show} successfully.', 'success')
    return redirect(url_for('booked'))

@app.route('/delete_booking/<int:booking_id>', methods=['POST'])
@login_required
def delete_booking(booking_id):
    booking = Bookings.query.get(booking_id)
    if booking is None:
      flash('Show does not exist or is already deleted','danger')
      return redirect(url_for('Dashboard'))
    elif booking.user_id!=current_user.user_id:
      flash('You do not own this show','danger')
      return redirect(url_for('Dashboard'))
    else:
      show_id=booking.show_id
      booking = Bookings.query.get(booking_id)
      tickets=booking.tickets
      show_id=booking.show_id
      update=db.session.query(Show).filter_by(show_id=show_id).first()
      update.seats_left=update.seats_left+tickets
      db.session.delete(booking)
      db.session.commit()
      flash(f'Booking for {booking.show} cancelled successfully','success')
      return redirect(url_for('Dashboard'))

@app.route('/editprofile', methods=['GET','POST'])
@login_required
def editprofile():
  if request.method=='GET':
    user=User.query.filter_by(user_id=current_user.user_id).first()
    return render_template('edit_profile.html', Name=user.username, email=user.email)

@app.route('/editname', methods=['POST'])
@login_required
def editname():
  if request.method=='POST':
    user=db.session.query(User).filter_by(user_id=current_user.user_id).first()
    name=request.form.get('username')
    if name and name!="":
      user.username=name
      flash("Username changed successfully",'success')
      db.session.commit()
    else:
      flash("Name cannot be null.",'danger')
    return redirect(url_for('editprofile'))

@app.route('/editmail', methods=['POST'])
@login_required
def editmail():
  if request.method=='POST':
    user=db.session.query(User).filter_by(user_id=current_user.user_id).first()
    Email = (request.form.get('Email')).lower()
    if Email != None:
      if re.search(eregex,Email):
        if not User.query.filter_by(email=Email).first():
          user.email=Email
          db.session.commit()
          flash("email changed successfully",'success')
          return redirect(url_for('editprofile'))
        else:
          flash("Another account already exists with this email id.",'danger')
          return redirect(url_for('editprofile'))
      else:
        flash("Email should resemble example@xyz.com.",'danger')
        return redirect(url_for('editprofile'))
    else:
      flash("Email should not be left blank.",'danger')
      return redirect(url_for('editprofile'))

@app.route('/editpass', methods=['POST'])
@login_required
def editpass():
  if request.method=='POST':
    user=db.session.query(User).filter_by(user_id=current_user.user_id).first()
    password=request.form.get('Password')
    new_pass=request.form.get('NewPassword')
    if bcrypt.check_password_hash(user.password,password):
      if re.search(pregex,new_pass):
        newpassword=bcrypt.generate_password_hash(new_pass)
        user.password=newpassword
        db.session.commit()
        flash("password changed successfully",'success')
        return redirect(url_for('editprofile'))
      else:
        flash("Password does not meet the standards",'danger')
        return redirect(url_for('editprofile'))
    else:
      flash("Wrong current password", 'danger')
      return redirect(url_for('editprofile'))

@app.route("/stat", methods=['GET', 'POST'])
@login_required
def stat():
  if request.method == 'GET':
    if current_user.level=="a":
      filter30days = datetime.now() - timedelta(days=30)
      bydate=db.session.query(func.DATE(Show.starttime), func.sum(Admin.seats - Show.seats_left)).join(Admin, Show.stage_id == Admin.stage_id).filter(Admin.user_id==current_user.user_id, Show.starttime >= filter30days).group_by(func.DATE(Show.starttime)).order_by(desc(Show.starttime)).all()
      dated = [row[0] for row in bydate]
      seatd = [row[1] for row in bydate]
      days30 = go.Figure()
      days30.add_trace(go.Scattergl(x=dated, y=seatd, mode='lines+markers', name='Seats booked'))
      days30.update_layout(title='Seats booked by Date', xaxis=dict(title='Date'), yaxis=dict(title='Seats booked'),width=800, height=400)
      last30 = days30.to_html(full_html=False)
      byshow=db.session.query(Show.show , func.sum(Admin.seats - Show.seats_left)).filter(Show.starttime >= filter30days).group_by(Show.show).order_by(desc(Show.starttime)).join(Admin, Show.stage_id == Admin.stage_id).all()
      shows = [row[0] for row in byshow]
      seats = [row[1] for row in byshow]
      show30d = go.Figure()
      show30d.add_trace(go.Bar(x=shows, y=seats, name='Seats booked for each show among all stages recently'))
      show30d.update_layout(title='Seats booked by Date', xaxis=dict(title='Date'), yaxis=dict(title='Seats booked'),width=800,height=400)
      show30s = show30d.to_html(full_html=False)
      byshowlocation = db.session.query(Show.show, Admin.location, func.sum(Admin.seats - Show.seats_left)).join(Admin, Show.stage_id == Admin.stage_id).filter(Show.starttime >= filter30days).group_by(Show.show, Admin.location).all()
      shows = sorted(set(row[0] for row in byshowlocation))
      locations = sorted(set(row[1] for row in byshowlocation))
      data = {location: [0] * len(shows) for location in locations}
      for row in byshowlocation:
        sindex = shows.index(row[0])
        data[row[1]][sindex] += row[2]
      traces = []
      for i, location in enumerate(locations):
        trace = go.Bar(x=shows,y=data[location],name=location,marker_color=f"rgba(50,{50+i*40},{150+i*30},0.8)")
        traces.append(trace)
      fig = go.Figure(data=traces)
      fig.update_layout(barmode='stack',title='Seats booked per show', xaxis={'categoryorder': 'total ascending','title':'Show'},yaxis=dict(title='Seats booked'),width=800,height=400)
      graph_html = fig.to_html(full_html=False)
      rshowcompute = db.session.query(Show.show,(Admin.seats - Show.seats_left) * Show.cost).join(Admin, Show.stage_id == Admin.stage_id).filter(Admin.user_id==current_user.user_id).all()
      rshow = db.session.query(Show.show,(Admin.seats - Show.seats_left) * Show.cost).join(Admin, Show.stage_id == Admin.stage_id).filter(Admin.user_id==current_user.user_id,Show.starttime >= filter30days).all()
      dater = [row[0] for row in rshow]
      seatr = [row[1] for row in rshow]
      rev30 = go.Figure()
      rev30.add_trace(go.Bar(x=dater, y=seatr, name='Revenue made'))
      rev30.update_layout(title='Revenue Splitup', xaxis=dict(title='Show'), yaxis=dict(title='Revenue'),width=800,height=400)
      revh30 = rev30.to_html(full_html=False)
      total_revenue = sum(revenue for show, revenue in rshowcompute)
      return render_template('stat.html', last30=last30, show30s=graph_html,total_revenue=total_revenue,revh30 = revh30)


if __name__ == '__main__':
  app.debug = True
  app.run(host='0.0.0.0', port=81)

