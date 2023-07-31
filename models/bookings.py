from . import db


class Bookings(db.Model):
  __tablename__ = 'bookings'
  booking_id = db.Column(db.Integer, nullable=False, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
  show_id = db.Column(db.Integer, db.ForeignKey("show.show_id"), nullable=False)
  show = db.Column(db.String, db.ForeignKey('show.show'), nullable=False)
  cost = db.Column(db.Integer, nullable=False)
  tickets = db.Column(db.Integer, nullable=False)
  rating = db.Column(db.Integer, nullable=False)  