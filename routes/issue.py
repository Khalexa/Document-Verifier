import os
from flask import Blueprint, render_template, request, current_app, redirect, url_for, flash, send_from_directory, session
from markupsafe import Markup
from models import db, Student, Certificate
from utils import generate_certificate_pdf, compute_sha256
import secrets
from models import DownloadToken

issue_bp = Blueprint("issue_bp", __name__)


@issue_bp.route("/issue", methods=["GET", "POST"])
def issue_certificate():

    if not session.get('admin_logged_in'):
        flash('Please log in as admin to access issuing.', 'error')
        return redirect(url_for('login'))

    if request.method == "POST":
        name = request.form.get("name")
        matric = request.form.get("matric")
        department = request.form.get("department")
        degree = request.form.get("degree")
        degree_class = request.form.get("degree_class")
        gpa = float(request.form.get("gpa", 0))
        graduation_year = int(request.form.get("graduation_year", 0))

        student = Student.query.filter_by(matric_number=matric).first()

        if not student:
            student = Student(
                matric_number=matric,
                full_name=name,
                department=department
            )
            db.session.add(student)
            db.session.commit()

        certificate = Certificate(
            student_id=student.id,
            degree_title=degree,
            degree_class=degree_class,
            gpa=gpa,
            graduation_year=graduation_year
        )

        db.session.add(certificate)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("Failed to save certificate to database.", "error")
            return redirect(url_for("issue_bp.issue_certificate"))

        pdf_filename = f"cert_{certificate.id}.pdf"
        pdf_path = os.path.join(current_app.config["CERT_FOLDER"], pdf_filename)

        try:
            generate_certificate_pdf(student, certificate, pdf_path)
            certificate.certificate_hash = compute_sha256(pdf_path)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("Certificate generated but failed to compute hash.", "error")
            return redirect(url_for("issue_bp.issue_certificate"))

        token = secrets.token_urlsafe(24)
        dt = DownloadToken(certificate_id=certificate.id, token=token)
        db.session.add(dt)
        db.session.commit()

        download_url = url_for('issue_bp.token_download', token=token)
        flash(Markup(f"Certificate issued successfully. <a href='{download_url}'>One-time download</a>"), "success")
        return render_template(
            "issue.html",
            issued=True,
            pdf_filename=pdf_filename
        )

    return render_template("issue.html")


@issue_bp.route('/certificate/<filename>')
def download_certificate(filename):
    from flask import session
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to download certificates.', 'error')
        return redirect(url_for('login'))

    return send_from_directory(current_app.config['CERT_FOLDER'], filename, as_attachment=True)


@issue_bp.route('/token-download/<token>')
def token_download(token):
    t = DownloadToken.query.filter_by(token=token).first()
    if not t or t.used:
        flash('Invalid or expired download link.', 'error')
        return redirect(url_for('index'))

    cert = Certificate.query.get(t.certificate_id)
    if not cert:
        flash('Certificate not found.', 'error')
        return redirect(url_for('index'))


    t.used = True
    db.session.commit()

    filename = f"cert_{cert.id}.pdf"
    return send_from_directory(current_app.config['CERT_FOLDER'], filename, as_attachment=True)
