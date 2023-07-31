from . import db

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
