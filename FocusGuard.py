import os
import time
import cv2
from gaze_tracking import GazeTracking


def play_video(video_path: str) -> None:
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"cannot open video: {video_path}")
        return

    # keep fps
    fps = cap.get(cv2.CAP_PROP_FPS)
    delay = int(1000 / fps) if fps and fps > 1 else 33

    cv2.namedWindow("Video", cv2.WINDOW_NORMAL)

    while True:
        ret, frame = cap.read()
        if not ret or frame is None or frame.size == 0:
            break

        cv2.imshow("Video", frame)

        key = cv2.waitKey(delay) & 0xFF
        if key == 27:  # esc
            break

    cap.release()
    cv2.destroyWindow("Video")


def main() -> None:
    gaze = GazeTracking()
    webcam = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not webcam.isOpened():
        print("cannot open webcam")
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(base_dir, "assets", "video.mp4")

    if not os.path.exists(video_path):
        print(f"video not found: {video_path}")
        webcam.release()
        return

    away_start_time = None
    away_threshold_sec = 5.0

    cv2.namedWindow("Demo", cv2.WINDOW_NORMAL)

    while True:
        ret, frame = webcam.read()
        if not ret or frame is None or frame.size == 0:
            print("cannot read webcam frame")
            break

        gaze.refresh(frame)
        new_frame = gaze.annotated_frame()

        status_text = ""
        center = gaze.is_center()
        left = gaze.is_left()
        right = gaze.is_right()

        if center:
            status_text = "Looking center"
            away_start_time = None
        else:
            if left:
                status_text = "Looking left"
            elif right:
                status_text = "Looking right"
            else:
                status_text = "Not looking center"

            if away_start_time is None:
                away_start_time = time.time()

        # countdown
        if away_start_time is not None:
            away_time = time.time() - away_start_time
            remaining = max(0.0, away_threshold_sec - away_time)

            cv2.putText(
                new_frame,
                f"Video in: {remaining:.1f}s",
                (60, 110),
                cv2.FONT_HERSHEY_DUPLEX,
                1.2,
                (0, 0, 255),
                2
            )

            if away_time >= away_threshold_sec:
                play_video(video_path)
                away_start_time = None

        cv2.putText(
            new_frame,
            status_text,
            (60, 60),
            cv2.FONT_HERSHEY_DUPLEX,
            1.5,
            (255, 0, 0),
            2
        )

        cv2.imshow("Demo", new_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # esc
            break

    webcam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()