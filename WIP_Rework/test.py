import os
import youtube_dl
from pyqt5.QtWidgets import (QApplication, QFormLayout, QHBoxLayout, QLineEdit, QProgressBar, QPushButton, QVBoxLayout, QWidget)


class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()

        # Create the GUI
        self.url_field = QLineEdit()
        self.download_button = QPushButton("Download")
        self.progress_bar = QProgressBar()

        layout = QFormLayout()
        layout.addRow("URL:", self.url_field)
        layout.addRow("Progress:", self.progress_bar)
        layout.addRow(self.download_button)
        self.setLayout(layout)

        # Connect the download button to the download handler
        self.download_button.clicked.connect(self.download_video)

    def download_video(self):
        # Get the URL of the video to download
        url = self.url_field.text()

        # Get the path to the Downloads folder
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")

        # Set up the youtube-dl options
        ydl_opts = {
            "outtmpl": os.path.join(downloads_path, "%(title)s.%(ext)s"),
            "progress_hooks": [self.update_progress],
        }

        # Download the video
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Reset the progress bar
        self.progress_bar.setValue(0)

    def update_progress(self, d):
        if d["status"] == "downloading":
            # Update the progress bar with the download progress
            self.progress_bar.setValue(int(d["_percent_str"].rstrip("%")))

    if __name__ == "__main__":
        app = QApplication([])
        window = YouTubeDownloader()
        window.show()
        app.exec_()
