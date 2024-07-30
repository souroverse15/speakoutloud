from flask import Flask, request, jsonify, render_template, send_from_directory
import smtplib
import os
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from werkzeug.utils import secure_filename
import yt_dlp
from celery import Celery


def update_yt_dlp():
    subprocess.run(["pip", "install", "-U", "yt-dlp"])


# Call the update function before starting the app
update_yt_dlp()

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "videos"
app.config.update(
    CELERY_BROKER_URL="redis://red-cqkh0u56l47c7384oq60:6379/0",
    CELERY_RESULT_BACKEND="redis://red-cqkh0u56l47c7384oq60:6379/0",
)

celery = Celery(app.name, broker=app.config["CELERY_BROKER_URL"])
celery.conf.update(app.config)


def download_video(url, filename):
    ydl_opts = {
        "outtmpl": os.path.join(app.config["UPLOAD_FOLDER"], filename),
        "format": "mp4",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


@celery.task()
def download_video_task(url, filename):
    download_video(url, filename)


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
            "faisalahmed191509@gmail.com"
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
        tasks = []

        for i, link in enumerate(evidence_links):
            video_filename = secure_filename(f"evidence_{i+1}.mp4")
            task = download_video_task.apply_async(args=[link, video_filename])
            tasks.append((task, video_filename))

        # Wait for tasks to complete
        for task, video_filename in tasks:
            try:
                task.get(timeout=300)  # Wait for up to 5 minutes
                filenames.append(video_filename)
            except Exception as e:
                errors.append(f"Error downloading video: {str(e)}")

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
            attachment.close()

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(email, password)
            text = msg.as_string()
            server.sendmail(email, recipients, text)
            server.quit()
        except Exception as e:
            return jsonify({"error": str(e)})

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
