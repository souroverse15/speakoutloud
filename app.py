from flask import Flask, request, jsonify, render_template, send_from_directory
import smtplib
import os
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import yt_dlp
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "videos"


def download_video(url, filename):
    ydl_opts = {
        "outtmpl": os.path.join(app.config["UPLOAD_FOLDER"], filename),
        "format": "mp4",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        evidence_links = request.form["evidence_links"].split()
        additional_recipients = (
            request.form["additional_recipients"].split(",")
            if request.form["additional_recipients"]
            else []
        )
        subject = request.form["subject"]
        body = request.form["body"]

        recipients = [
            "dihan010@gmail.com"
            # "motazazaiza9@gmail.com",
            # "ungsc-hr@un.org",
            # "liaison@un.org",
            # "unictf-liaison@un.org",
            # "ungsc-cslc@un.org",
            # "scustomerservice@un.org",
            # "ftssm@un.org",
            # "gsc-osh@un.org",
            # "ungsc-information@un.org",
            # "newsonline@bbc.co.uk",
            # "cnn.feedback@cnn.com",
            # "contactus@aljazeera.net",
            # "editor@reuters.com",
            # "info@ap.org",
            # "news@skynews.com",
            # "observers@france24.com",
            # "feedback@dw.com",
            # "editor@bloomberg.net",
            # "info@nhk.or.jp",
            # "ungsccommunicationunit@un.org",
            # "everydaypalestine@gmail.com",
            # "MansourShoumanTalks@gmail.com",
            # "connect.to.ase@gmail.com",
            # "princekouta5@gmail.com",
            # "management.anat@gmail.com",
            # "Hind.khoudary@gmail.com",
            # "Ecollab@plestiaalaqad.com",
            # "dearwhitestaffer@gmail.com",
            # "ig@islamify.org",
        ] + additional_recipients

        errors = []
        filenames = []
        for i, link in enumerate(evidence_links):
            try:
                video_filename = secure_filename(f"evidence_{i+1}.mp4")
                download_video(link, video_filename)
                filenames.append(video_filename)
            except Exception as e:
                errors.append(f"Error downloading {link}: {str(e)}")

        if errors:
            return jsonify({"errors": errors})

        msg = MIMEMultipart()
        msg["From"] = email
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        for video_filename in filenames:
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], video_filename)
            attachment = open(filepath, "rb")

            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", f"attachment; filename= {video_filename}"
            )

            msg.attach(part)
            attachment.close()  # Ensure the file is properly closed

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(email, password)
            text = msg.as_string()
            server.sendmail(email, recipients, text)
            server.quit()
        except Exception as e:
            return jsonify({"error": str(e)})

        # Delete the video files after sending the email
        for video_filename in filenames:
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], video_filename)
            os.remove(filepath)

        return jsonify({"success": "Emails sent successfully!"})

    return render_template("index.html")


@app.route("/success")
def success():
    return "Emails sent successfully!"


@app.route("/videos/<filename>")
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"])
    app.run(debug=True)
