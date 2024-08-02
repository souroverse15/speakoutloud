from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
import os
import yt_dlp
from werkzeug.utils import secure_filename
import threading

app = Flask(__name__)
socketio = SocketIO(app)

# Define a list of recipient emails
recipient_emails = [
    "faisalahmed191509@gmail.com",
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
]


def download_video(url, filename):
    ydl_opts = {
        "outtmpl": filename,
        "format": "mp4",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def download_videos(urls, batch_size=5):
    for i in range(0, len(urls), batch_size):
        batch = urls[i : i + batch_size]
        for j, url in enumerate(batch):
            video_filename = secure_filename(f"evidence_{i + j + 1}.mp4")
            try:
                download_video(url, video_filename)
                socketio.emit(
                    "progress", {"video": video_filename, "status": "completed"}
                )
            except Exception as e:
                socketio.emit(
                    "progress", {"video": video_filename, "status": f"error: {str(e)}"}
                )


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

        # Combine hardcoded recipient emails with additional recipients from the form
        recipients = recipient_emails + additional_recipients

        # Start the video download in a separate thread
        threading.Thread(target=download_videos, args=(evidence_links, 5)).start()

        return jsonify({"success": "Videos are being processed!"})

    return render_template("index.html")


if __name__ == "__main__":
    socketio.run(app, debug=True)
