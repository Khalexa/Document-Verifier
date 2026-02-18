from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    matric_number = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable = False)
    certificate = db.relationship('Certificate', backref='student', lazy=True)

class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    degree_title = db.Column(db.String(50), nullable = False)
    degree_class = db.Column (db.String(50), nullable = False)
    gpa = db.Column(db.Float, nullable = False)
    graduation_year = db.Column(db.Integer, nullable=True)
    date_issued = db.Column(db.DateTime, default= datetime.utcnow)
    certificate_hash = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(10), default = 'valid')

class VerificationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uploaded_filename = db.Column(db.String(100))
    extracted_name = db.Column(db.String(100))
    extracted_matric = db.Column(db.String(20))
    db_match = db.Column (db.Boolean)
    hash_match = db.Column(db.Boolean)
    confidence_score = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default = datetime.utcnow)
    

class DownloadToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    certificate_id = db.Column(db.Integer, db.ForeignKey('certificate.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
