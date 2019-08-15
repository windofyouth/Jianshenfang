from . import db
from datetime import datetime


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    role = db.Column(db.String(64))
    referrer = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    # referrer_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    # referrers = db.relationship('Student', backref='referrer', lazy='dynamic')


class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True)
    leader = db.Column(db.String(64), index=True, unique=True)
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow)
    students = db.relationship('Student', backref='team', lazy='dynamic')
