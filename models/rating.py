from . import db


class Rating(db.Model):
  __tablename__ = 'rating'
  show = db.Column(db.String, db.ForeignKey('show.show'), primary_key=True, nullable=False)
  rating = db.Column(db.Float, nullable=False)
  stars = db.Column(db.Integer, nullable=False)
  count = db.Column(db.Integer, nullable=False)
