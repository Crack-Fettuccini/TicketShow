from . import db


class Request(db.Model):
  __tablename__ = 'request'
  email = db.Column(db.String, db.ForeignKey("user.email"), nullable=False, primary_key=True)
