import os
from flask import Blueprint, render_template, request, current_app, redirect, url_for, flash
from models import db, Student, Certificate
from utils import generate_certificate_pdf, compute_sha256

issue_bp = Blueprint("issue_bp", __name__)


@issue_bp.route("/issue", methods=["GET", "POST"])
def issue_certificate():

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
        db.session.commit()

        pdf_filename = f"cert_{certificate.id}.pdf"
        pdf_path = os.path.join(current_app.config["CERT_FOLDER"], pdf_filename)

        generate_certificate_pdf(student, certificate, pdf_path)

        certificate.certificate_hash = compute_sha256(pdf_path)
        db.session.commit()

        flash("Certificate issued successfully.", "success")
        return redirect(url_for("issue_bp.issue_certificate"))

    return render_template("issue.html")
