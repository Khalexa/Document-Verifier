from flask import Flask, render_template, request, redirect, url_for, flash, session
from config import Config
from models import db, Student, Certificate, VerificationLog
from utils import compute_sha256, extract_text, parse_certificate_text
import os

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CERT_FOLDER'], exist_ok=True)

db.init_app(app)

# Initialize DB (run once)
with app.app_context():
    db.create_all()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pw = request.form.get('password')
        if pw and pw == app.config.get('ADMIN_PASSWORD'):
            session['admin_logged_in'] = True
            flash('Logged in as admin.', 'success')
            return redirect(url_for('issue_bp.issue_certificate'))
        else:
            flash('Invalid password.', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('Logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/admin')
def admin_panel():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to view the admin panel.', 'error')
        return redirect(url_for('login'))

    certs = Certificate.query.order_by(Certificate.id.desc()).all()
    logs = VerificationLog.query.order_by(VerificationLog.timestamp.desc()).limit(100).all()
    return render_template('admin.html', certs=certs, logs=logs)


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    file_hash = compute_sha256(filepath)
    text = extract_text(filepath)

    parsed = parse_certificate_text(text)

    extracted_name = parsed.get("name")
    extracted_matric = parsed.get("matric_number")
    extracted_year = parsed.get("graduation_year")
    certificate_id = parsed.get("certificate_id")

    cert = None
    if certificate_id:
        cert = Certificate.query.get(certificate_id)

    if cert:
        db_match = (
            cert.student.full_name == extracted_name and
            cert.student.matric_number == extracted_matric and
            cert.graduation_year == extracted_year
        )

        hash_match = (cert.certificate_hash == file_hash)

        confidence = 0
        if db_match:
            confidence += 60
        if hash_match:
            confidence += 40
    else:
        db_match = False
        hash_match = False
        confidence = 0

    log = VerificationLog(
        uploaded_filename=file.filename,
        extracted_name=extracted_name,
        extracted_matric=extracted_matric,
        db_match=db_match,
        hash_match=hash_match,
        confidence_score=confidence
    )

    db.session.add(log)
    db.session.commit()

    return render_template("result.html",
    confidence=confidence,
    db_match=db_match,
    hash_match=hash_match)


from routes.issue import issue_bp
from routes.verify import verify_bp

app.register_blueprint(issue_bp)
app.register_blueprint(verify_bp)


if __name__ == "__main__":
    app.run(debug=True)
