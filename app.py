from quart import Quart, request, jsonify, render_template
from quart_socketio import SocketIO, emit
import os
import yt_dlp
from werkzeug.utils import secure_filename
import asyncio
import httpx

app = Quart(__name__)
socketio = SocketIO(app)

recipient_emails = [
    
    "motazazaiza9@gmail.com",
    "ungsc-hr@un.org",
    "liaison@un.org",
    "unictf-liaison@un.org",
    "ungsc-cslc@un.org",
    "scustomerservice@un.org",
    "ftssm@un.org",
    "gsc-osh@un.org",
    "ungsc-information@un.org",
    "newsonline@bbc.co.uk",
    "cnn.feedback@cnn.com",
    "contactus@aljazeera.net",
    "editor@reuters.com",
    "info@ap.org",
    "news@skynews.com",
    "observers@france24.com",
    "feedback@dw.com",
    "editor@bloomberg.net",
    "info@nhk.or.jp",
    "ungsccommunicationunit@un.org",
    "everydaypalestine@gmail.com",
    "MansourShoumanTalks@gmail.com",
    "connect.to.ase@gmail.com",
    "princekouta5@gmail.com",
    "management.anat@gmail.com",
    "Hind.khoudary@gmail.com",
    "Ecollab@plestiaalaqad.com",
    "dearwhitestaffer@gmail.com",
    "ig@islamify.org",
]


async def download_video(url, filename):
    ydl_opts = {
        "outtmpl": filename,
        "format": "mp4",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


async def download_videos(urls, batch_size=5):
    for i in range(0, len(urls), batch_size):
        batch = urls[i : i + batch_size]
        tasks = [
            download_video(url, secure_filename(f"evidence_{i + j + 1}.mp4"))
            for j, url in enumerate(batch)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for j, result in enumerate(results):
            video_filename = secure_filename(f"evidence_{i + j + 1}.mp4")
            if isinstance(result, Exception):
                await socketio.emit(
                    "progress",
                    {"video": video_filename, "status": f"error: {str(result)}"},
                )
            else:
                await socketio.emit(
                    "progress", {"video": video_filename, "status": "completed"}
                )


@app.route("/", methods=["GET", "POST"])
async def index():
    if request.method == "POST":
        form = await request.form
        email = form["email"]
        password = form["password"]
        evidence_links = form["evidence_links"].split()
        additional_recipients = (
            form["additional_recipients"].split(",")
            if form["additional_recipients"]
            else []
        )
        subject = form["subject"]
        body = form["body"]

        # Combine hardcoded recipient emails with additional recipients from the form
        recipients = recipient_emails + additional_recipients

        # Start the video download asynchronously
        asyncio.create_task(download_videos(evidence_links, 5))

        return jsonify({"success": "Videos are being processed!"})

    return await render_template("index.html")


if __name__ == "__main__":
    socketio.run(app, debug=True)
