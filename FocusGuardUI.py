import os
import time
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from gaze_tracking import GazeTracking


class FocusGuardApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("FocusGuard")
        self.root.geometry("420x220")
        self.root.resizable(False, False)

        # core state
        self.focus_enabled = False
        self.selected_video_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "assets",
            "video.mp4"
        )

        self.away_start_time = None
        self.away_threshold_sec = 5.0
        self.is_video_playing = False

        # tracking objects
        self.gaze = GazeTracking()
        self.webcam = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        if not self.webcam.isOpened():
            messagebox.showerror("Error", "Cannot open webcam")
            self.root.destroy()
            return

        # ui
        self.title_label = tk.Label(root, text="FocusGuard", font=("Arial", 16, "bold"))
        self.title_label.pack(pady=(12, 8))

        self.toggle_button = tk.Button(
            root,
            text="Focus: OFF",
            width=20,
            height=2,
            command=self.toggle_focus
        )
        self.toggle_button.pack(pady=6)

        self.choose_button = tk.Button(
            root,
            text="Choose Video",
            width=20,
            height=2,
            command=self.choose_video
        )
        self.choose_button.pack(pady=6)

        self.video_label = tk.Label(
            root,
            text=self.get_video_label_text(),
            wraplength=380,
            justify="center"
        )
        self.video_label.pack(pady=(8, 4))

        self.status_label = tk.Label(
            root,
            text="Status: idle",
            font=("Arial", 11)
        )
        self.status_label.pack(pady=(4, 8))

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # start update loop
        self.root.after(30, self.process_frame)

    def get_video_label_text(self) -> str:
        if self.selected_video_path and os.path.exists(self.selected_video_path):
            return f"Video: {os.path.basename(self.selected_video_path)}"
        return "Video: not selected"

    def toggle_focus(self) -> None:
        self.focus_enabled = not self.focus_enabled

        if self.focus_enabled:
            self.toggle_button.config(text="Focus: ON")
            self.status_label.config(text="Status: tracking active")
            self.away_start_time = None
        else:
            self.toggle_button.config(text="Focus: OFF")
            self.status_label.config(text="Status: tracking paused")
            self.away_start_time = None

    def choose_video(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Choose video",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            self.selected_video_path = file_path
            self.video_label.config(text=self.get_video_label_text())

    def play_video(self, video_path: str) -> None:
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            self.status_label.config(text="Status: cannot open selected video")
            return

        self.is_video_playing = True
        self.status_label.config(text="Status: video playing")

        fps = cap.get(cv2.CAP_PROP_FPS)
        delay = int(1000 / fps) if fps and fps > 1 else 33

        cv2.namedWindow("Video", cv2.WINDOW_NORMAL)

        while True:
            ret, frame = cap.read()
            if not ret or frame is None or frame.size == 0:
                break

            cv2.imshow("Video", frame)

            key = cv2.waitKey(delay) & 0xFF
            if key == 27:
                break

        cap.release()
        cv2.destroyWindow("Video")

        self.is_video_playing = False
        self.away_start_time = None

        if self.focus_enabled:
            self.status_label.config(text="Status: tracking active")
        else:
            self.status_label.config(text="Status: tracking paused")

    def process_frame(self) -> None:
        if not self.webcam or not self.webcam.isOpened():
            return

        ret, frame = self.webcam.read()
        if not ret or frame is None or frame.size == 0:
            self.status_label.config(text="Status: cannot read webcam frame")
            self.root.after(100, self.process_frame)
            return

        if self.focus_enabled and not self.is_video_playing:
            self.gaze.refresh(frame)

            center = self.gaze.is_center()
            left = self.gaze.is_left()
            right = self.gaze.is_right()

            if center:
                self.away_start_time = None
                self.status_label.config(text="Status: looking center")
            else:
                if self.away_start_time is None:
                    self.away_start_time = time.time()

                away_time = time.time() - self.away_start_time
                remaining = max(0.0, self.away_threshold_sec - away_time)

                if left:
                    self.status_label.config(text=f"Status: looking left | video in {remaining:.1f}s")
                elif right:
                    self.status_label.config(text=f"Status: looking right | video in {remaining:.1f}s")
                else:
                    self.status_label.config(text=f"Status: not looking center | video in {remaining:.1f}s")

                if away_time >= self.away_threshold_sec:
                    if self.selected_video_path and os.path.exists(self.selected_video_path):
                        self.play_video(self.selected_video_path)
                    else:
                        self.status_label.config(text="Status: video file not found")
                        self.away_start_time = None

        # optional debug preview window
        debug_frame = self.gaze.annotated_frame() if self.focus_enabled else frame
        cv2.imshow("Camera Preview", debug_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            self.on_close()
            return

        self.root.after(30, self.process_frame)

    def on_close(self) -> None:
        if self.webcam and self.webcam.isOpened():
            self.webcam.release()

        cv2.destroyAllWindows()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = FocusGuardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()