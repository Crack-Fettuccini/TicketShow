from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from flask_login import current_user, login_required
import re
from datetime import datetime, time
from pytz import timezone
from models import db, User, Admin, Show, Rating, Request, Bookings
from .. import IST, eregex, pregex, bcrypt

user_bp = Blueprint('user', __name__, template_folder='../templates', static_folder="../static")


@user_bp.route('/sellerpermissions')
@login_required
def sellerpermissions():
    flash("Seller permissions has been requested.",'danger')
    DoesNotExist = (db.session.query(Request).filter_by(email=current_user.email).first() is None)
    if DoesNotExist:
      req=Request(email=current_user.email)
      db.session.add(req)
      db.session.commit()
    return redirect(url_for('user.Dashboard'))

@user_bp.route("/Dashboard", methods=['GET', 'POST'])
@login_required
def Dashboard():
  if request.method == 'GET':
    if current_user.level=="b":
      events = db.session.query(Show, Rating.rating, Admin.location).join(Rating, Show.show == Rating.show, isouter=True).join(Admin, Show.stage_id == Admin.stage_id, isouter=True).filter(Show.endtime >= datetime.now(timezone('Asia/Kolkata'))).all()
      session['location']="None"
      session['rating']="None"
      session['date']=""
      session['tags']="None"
      return render_template('user_buyer.html', events=events, Locations = [locations.location for locations in Admin.query.distinct(Admin.location).all()])
    else:
      return redirect(url_for('login.login',signup='login'))
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



@user_bp.route("/booktickets/<int:show_id>", methods=['GET', 'POST'])
@login_required
def book(show_id):
  if request.method == 'GET':
    show=Show.query.get(show_id)
    venue= Admin.query.get(show.stage_id)
    location=venue.location
    if IST.localize(show.endtime)> datetime.now(timezone('Asia/Kolkata')):
      return render_template('book.html',show=show,location=location)
    else:
      return redirect(url_for('user.Dashboard'))
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
        return redirect(url_for('user.Dashboard'))
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
        return redirect(url_for('user.Dashboard'))
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
      return redirect(url_for('user.Dashboard'))

@user_bp.route("/bookedtickets/", methods=['GET', 'POST'])
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

@user_bp.route("/rating/<int:booking_id>", methods=['POST'])
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
    return redirect(url_for('user.booked'))

@user_bp.route('/delete_booking/<int:booking_id>', methods=['POST'])
@login_required
def delete_booking(booking_id):
    booking = Bookings.query.get(booking_id)
    if booking is None:
      flash('Show does not exist or is already deleted','danger')
      return redirect(url_for('user.Dashboard'))
    elif booking.user_id!=current_user.user_id:
      flash('You do not own this show','danger')
      return redirect(url_for('user.Dashboard'))
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
      return redirect(url_for('user.Dashboard'))

@user_bp.route('/editprofile', methods=['GET','POST'])
@login_required
def editprofile():
  if request.method=='GET':
    user=User.query.filter_by(user_id=current_user.user_id).first()
    return render_template('edit_profile.html', Name=user.username, email=user.email)

@user_bp.route('/editname', methods=['POST'])
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
    return redirect(url_for('user.editprofile'))

@user_bp.route('/editmail', methods=['POST'])
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
          return redirect(url_for('user.editprofile'))
        else:
          flash("Another account already exists with this email id.",'danger')
          return redirect(url_for('user.editprofile'))
      else:
        flash("Email should resemble example@xyz.com.",'danger')
        return redirect(url_for('user.editprofile'))
    else:
      flash("Email should not be left blank.",'danger')
      return redirect(url_for('user.editprofile'))

@user_bp.route('/editpass', methods=['POST'])
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
        return redirect(url_for('user.editprofile'))
      else:
        flash("Password does not meet the standards",'danger')
        return redirect(url_for('user.editprofile'))
    else:
      flash("Wrong current password", 'danger')
      return redirect(url_for('user.editprofile'))

