from . import db

class Admin(db.Model):
  __tablename__ = 'admin'
  stage_id = db.Column(db.Integer,autoincrement=True, primary_key=True, nullable=False)
  user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
  location = db.Column(db.String)
  stage = db.Column(db.String, nullable=False)
  seats = db.Column(db.Integer, nullable=False)
