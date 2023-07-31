from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from sqlalchemy import func, desc
from flask_login import current_user, login_required
import plotly.graph_objects as go
import re
from datetime import datetime, timedelta
from pytz import timezone
from models import db, User, Admin, Show, Rating, Request, Bookings
from .. import IST, eregex, pregex, bcrypt

admin_bp = Blueprint('admin', __name__, template_folder='../templates', static_folder='../static')


@admin_bp.route("/Dashboard", methods=['GET'])
@login_required
def Dashboard():
  if request.method == 'GET':
    if current_user.level=="a":
      return render_template('A_user_seller.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id).all())  
    else:
      return redirect(url_for('login.login',signup='login'))
@admin_bp.route('/delete_show/<int:show_id>', methods=['POST'])
@login_required
def delete_show(show_id):
    show = Show.query.get(show_id)
    if show is None:
      return redirect(url_for('admin.admin.Dashboard'))
    elif show.user_id!=current_user.user_id:
      return redirect(url_for('admin.Dashboard'))
    else:
      db.session.delete(show)
      allbook=db.session.query(Bookings).filter_by(show_id=show_id).all()
      for book in allbook:
        db.session.delete(book)
      db.session.commit()
      flash(f'{show.show} deleted successfully!', 'success')
      return redirect(url_for('admin.Dashboard'))

@admin_bp.route('/delete_venue/<int:stage_id>', methods=['POST'])
@login_required
def delete_venue(stage_id):
  stage = Admin.query.get(stage_id)
  if current_user.user_id==stage.user_id:
    if stage is None:
      return redirect(url_for('admin.Dashboard'))
    elif stage.user_id!=current_user.user_id:
      flash('You do not own this stage', 'danger')
      return redirect(url_for('admin.Dashboard'))
    shows=db.session.query(Show).filter_by(stage_id=stage_id).filter(Show.endtime>datetime.now()).all()
    if shows:
      flash('There are shows planned for this place, delete the shows before you delete the venue.', 'danger')
      return redirect(url_for('admin.Dashboard'))
    else:
      flash(f'{stage.stage} deleted successfully!', 'success')
      db.session.delete(stage)
      db.session.commit()
      return redirect(url_for('admin.Dashboard'))
  else:
    return redirect(url_for('admin.Dashboard'))

@admin_bp.route('/edit_show/<int:show_id>', methods=['GET','POST'])
@login_required
def edit_show(show_id):
  show = Show.query.get(show_id)
  if current_user.user_id==show.user_id:
    if request.method == 'GET':
      stage_id=Show.stage_id
      show=Show.query.filter_by(show_id=show_id).first()
      return render_template('A_editshow.html',stage_id=stage_id,venues=db.session.query(Admin).filter_by(user_id=current_user.user_id, location=(Admin.query.get(show.stage_id)).location), venue=show.stage_id, show=show.show, start=show.starttime, end=show.endtime, cost=show.cost, tag=show.tags)
    if request.method == 'POST':
      stage=request.form.get('Venue')
      show=request.form.get('Show')
      cost=int(request.form.get('cost'))
      tags=request.form.get('Genre')
      if not cost:
        flash('Please enter cost of ticket',"danger")
        return render_template('A_editshow.html',stage_id=stage_id,venues=db.session.query(Admin).filter_by(user_id=current_user.user_id, location=(Admin.query.get(show.stage_id)).location), venue=show.stage_id, show=show.show, start=show.starttime, end=show.endtime, cost=show.cost, tag=show.tags)
      elif cost<0:
        flash('Cost should not be negative',"danger")
        return render_template('A_editshow.html',stage_id=stage_id,venues=db.session.query(Admin).filter_by(user_id=current_user.user_id, location=(Admin.query.get(show.stage_id)).location), venue=show.stage_id, show=show.show, start=show.starttime, end=show.endtime, cost=show.cost, tag=show.tags)
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
          return redirect(url_for('admin.Dashboard'))
        else:
          flash('Booked tickets exceed the capacity for the new venue to accomodate.', 'danger')
          return render_template('A_editshow.html',stage_id=stage_id,venues=db.session.query(Admin).filter_by(user_id=current_user.user_id, location=(Admin.query.get(show.stage_id)).location), venue=show.stage_id, show=show.show, start=show.starttime, end=show.endtime, cost=show.cost, tag=show.tags)
        
  else:
    return redirect(url_for('admin.Dashboard'))
    
@admin_bp.route('/editvenue/<int:stage_id>', methods=['GET','POST'])
@login_required
def editvenue(stage_id):
  if request.method=='GET':
    venue=Admin.query.filter_by(stage_id=stage_id).filter(Admin.user_id==current_user.user_id).first()
    if venue:
      return render_template('A_editvenue.html',Stage=venue.stage,Seat=venue.seats,Location=venue.location)
    else:
      flash("You do not own this stage!",'danger')
      return redirect(url_for('admin.Dashboard'))
  elif request.method=='POST':
    stage=request.form.get('Venue')
    seat=request.form.get('Capacity')
    if not stage:
      flash('Please enter venue name.',"danger")
      return render_template('A_editvenue.html')
    if not seat:
      flash('Please enter number of seats.',"danger")
      return render_template('A_editvenue.html')
    seat=int(seat)
    if seat<0:
      flash('Seats should not be negative.',"danger")
      return render_template('A_editvenue.html')
    venue=db.session.query(Admin).filter_by(stage_id=stage_id).filter(Admin.user_id==current_user.user_id).first()

    if venue:
      venue.stage=stage
      if venue.seats>seat:
        flash('Seats should not be lesser than current number of seats.',"danger")
        return render_template('A_newvenue.html')
      flash('Venue modified successfully',"success")
      update_stmt = db.session.query(Show).filter(Show.stage_id == venue.stage_id,Show.starttime > datetime.now()).update({"stage":venue.stage,"seats_left": Show.seats_left + (seat-venue.seats)})
      venue.seats=seat
      db.session.commit()
    return redirect(url_for('admin.Dashboard'))


@admin_bp.route('/editshows/<int:stage_id>', methods=['GET', 'POST'])
@login_required
def editshows(stage_id):
  return render_template('A_editshows.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id, location=(Admin.query.get(stage_id)).location),stage_id=stage_id,stage=(db.session.query(Admin).filter_by(stage_id=stage_id).first()).stage,events=db.session.query(Show).filter_by(user_id=current_user.user_id).filter(Show.endtime >= datetime.now(timezone('Asia/Kolkata'))).filter(Show.stage_id == stage_id).all())

@admin_bp.route('/newvenue', methods=['GET', 'POST'])
@login_required
def newvenue():
  if request.method=='GET':
    return render_template('A_newvenue.html')
  elif request.method=='POST':
    stage=request.form.get('Venue')
    seat=request.form.get('Capacity')
    location=request.form.get('Location')
    if not stage:
      flash('Please enter stage name.',"danger")
      return render_template('A_newvenue.html')
    if not seat:
      flash('Please enter number of seats.',"danger")
      return render_template('A_newvenue.html')
    if not location:
      flash('Please enter location.',"danger")
      return render_template('A_newvenue.html')
    seat=int(seat)
    if seat<0:
      flash('Seats should not be negative',"danger")
      return render_template('A_newvenue.html')
    venues=db.session.query(Admin).filter_by(user_id=current_user.user_id).filter(Admin.stage==stage).filter(Admin.seats==seat).filter(Admin.location==location).first()
    if venues is not None:
      flash('Venue already exists',"danger")
      return render_template('A_newvenue.html')
    else:
      seat=int(seat)
      new_venue=Admin(user_id=current_user.user_id,location=location,stage=stage,seats=seat)
      db.session.add(new_venue)
      db.session.commit()
      flash(f'{new_venue.stage} has been added successfully','success')
      return redirect(url_for('admin.Dashboard'))
    
@admin_bp.route("/newshow", methods=['GET', 'POST'])
@login_required
def newshow():
  if request.method == 'GET':
    return render_template('A_newshow.html', venues=db.session.query(Admin).filter_by(user_id=current_user.user_id).all())
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
      return render_template('A_newshow.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id).all())
    if start>end:
      flash('Start time should be before end time',"danger")
      return render_template('A_newshow.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id).all())
    if start<=datetime.now(timezone('Asia/Kolkata')) or end<=datetime.now(timezone('Asia/Kolkata')):
      flash('You cannot add shows to the past, we do not provide time machines.',"danger")
      return render_template('A_newshow.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id).all())
    if not cost:
        flash('Please enter cost of ticket',"danger")
        return render_template('A_newshow.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id).all())
    elif cost<0:
      flash('Cost should not be negative',"danger")
      return render_template('A_newshow.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id).all())
    stage = int(stage)
    venue=db.session.query(Admin).filter_by(user_id=current_user.user_id).filter(Admin.stage_id==stage).first()
    if venue is not None:
      new_show=Show(user_id=current_user.user_id, stage_id=venue.stage_id, starttime=start, endtime=end, stage=venue.stage, show=show, seats_left=venue.seats, cost=cost, tags=tags)
      clashing = db.session.query(Show).filter_by(user_id=current_user.user_id).filter(((Show.starttime <= start) & (Show.endtime >= start)) | ((Show.starttime <= end) & (Show.endtime >= end))).filter(Show.stage_id==stage).first()
      if clashing:
        err='New show timing clashes with '+clashing.show+' starting at '+(clashing.starttime).strftime("%m/%d/%Y, %H:%M:%S")+'.'
        flash(err,"danger")
        return render_template('A_newshow.html',venues=db.session.query(Admin).filter_by(user_id=current_user.user_id).all())
      else:
        db.session.add(new_show)
        db.session.commit()
        stage_id=new_show.stage_id
        flash(f'{new_show.show} has been added succesfully','success')
        return redirect(url_for('admin.editshows',stage_id=stage_id))


@admin_bp.route('/editprofile', methods=['GET','POST'])
@login_required
def editprofile():
  if request.method=='GET':
    user=User.query.filter_by(user_id=current_user.user_id).first()
    return render_template('A_edit_profile.html', Name=user.username, email=user.email)

@admin_bp.route('/editname', methods=['POST'])
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
    return redirect(url_for('admin.editprofile'))

@admin_bp.route('/editmail', methods=['POST'])
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
          return redirect(url_for('admin.editprofile'))
        else:
          flash("Another account already exists with this email id.",'danger')
          return redirect(url_for('admin.editprofile'))
      else:
        flash("Email should resemble example@xyz.com.",'danger')
        return redirect(url_for('admin.editprofile'))
    else:
      flash("Email should not be left blank.",'danger')
      return redirect(url_for('admin.editprofile'))

@admin_bp.route('/editpass', methods=['POST'])
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
        return redirect(url_for('admin.editprofile'))
      else:
        flash("Password does not meet the standards",'danger')
        return redirect(url_for('admin.editprofile'))
    else:
      flash("Wrong current password", 'danger')
      return redirect(url_for('admin.editprofile'))

@admin_bp.route("/stat", methods=['GET', 'POST'])
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
      return render_template('A_stat.html', last30=last30, show30s=graph_html,total_revenue=total_revenue,revh30 = revh30)
