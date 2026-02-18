import os
from flask import Blueprint, render_template, request, current_app, flash
from models import db, Certificate, VerificationLog
# import utils inside the request handler to avoid import-time dependency issues

verify_bp = Blueprint("verify_bp", __name__)


@verify_bp.route("/verify", methods=["GET", "POST"])
def verify_certificate():

    if request.method == "POST":
        # local imports to avoid importing heavy binary deps during module import
        from utils import compute_sha256, extract_text, parse_certificate_text, similarity

        file = request.files.get("file")
        if not file:
            return render_template("verify.html", error="No file uploaded")

        upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], file.filename)
        file.save(upload_path)

        file_hash = compute_sha256(upload_path)
        extracted_text = extract_text(upload_path)
        parsed_data = parse_certificate_text(extracted_text)

        certificate_id = parsed_data.get("certificate_id")
        extracted_name = parsed_data.get("name")
        extracted_matric = parsed_data.get("matric_number")
        extracted_year = parsed_data.get("graduation_year")

        certificate = None
        if certificate_id:
            certificate = Certificate.query.get(certificate_id)
        if not certificate:
            certificate = Certificate.query.filter_by(certificate_hash=file_hash).first()
            if certificate:
                flash("Certificate record located by hash.", "info")

        if certificate:
            name_match = similarity(certificate.student.full_name, extracted_name) > 0.85
            matric_match = certificate.student.matric_number == extracted_matric
            year_match = (certificate.graduation_year == extracted_year)

            db_match = name_match and matric_match and year_match
            hash_match = certificate.certificate_hash == file_hash

            if hash_match and not db_match:
                db_match = True 
                flash("Hash matched; DB record considered valid despite parsing differences.", "info")

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

        return render_template(
            "verification_result.html",
            db_match=db_match,
            hash_match=hash_match,
            confidence=confidence
        )

    return render_template("verify.html")
