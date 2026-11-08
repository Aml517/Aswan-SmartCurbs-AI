"""Unified video capture source supporting file, continuous replay, webcam, and RTSP stream modes.

Designed for Aswan SmartCurbs AI:
- 'file': Standard single-pass video processing (backward compatible).
- 'replay': Continuous looping video stream at real-time video FPS.
- 'webcam': Physical local camera by device index with reconnection handling.
- 'rtsp': Remote IP-camera / CCTV stream with timeout and reconnection handling.
"""
import logging
import os
import time
from pathlib import Path
from typing import Optional, Tuple, Union

import cv2
import numpy as np

try:
    from common import CFG, path
except ImportError:
    from ai.common import CFG, path

logger = logging.getLogger(__name__)


class VideoSource:
    """Configurable video source supporting file, replay, webcam, and RTSP modes."""

    VALID_MODES = ("file", "replay", "webcam", "rtsp", "windy")

    def __init__(
        self,
        mode: Optional[str] = None,
        source: Optional[Union[str, int]] = None,
        cfg: Optional[dict] = None,
        reconnect_attempts: Optional[int] = None,
        reconnect_delay_sec: Optional[float] = None,
        target_fps: Optional[float] = None,
    ):
        self.cfg = cfg or CFG
        src_cfg = self.cfg.get("source", {})

        # Resolve mode
        self.mode = str(mode or src_cfg.get("mode") or "file").lower().strip()
        if self.mode not in self.VALID_MODES:
            raise ValueError(f"Invalid mode '{self.mode}'. Must be one of {self.VALID_MODES}")

        # Resolve source target (environment variable LIVE_STREAM_URL has highest precedence for live streams)
        env_stream = os.getenv("LIVE_STREAM_URL")
        self.source = source
        if self.source is None:
            if self.mode in ("rtsp", "windy") and env_stream:
                self.source = env_stream
            elif self.mode in ("file", "replay"):
                self.source = src_cfg.get("video_path") or self.cfg.get("video") or "data/input.mp4"
            elif self.mode == "webcam":
                self.source = src_cfg.get("webcam_index", 0)
            elif self.mode == "rtsp":
                self.source = env_stream or src_cfg.get("rtsp_url", "https://s5.webcamromania.ro/tljurilovca/index.m3u8")
            elif self.mode == "windy":
                self.source = env_stream or src_cfg.get("windy_webcam_id") or self.cfg.get("windy", {}).get("webcam_id", "1793889300")

        # Configuration options
        self.reconnect_attempts = int(
            reconnect_attempts
            if reconnect_attempts is not None
            else src_cfg.get("reconnect_attempts", 3)
        )
        self.reconnect_delay_sec = float(
            reconnect_delay_sec
            if reconnect_delay_sec is not None
            else src_cfg.get("reconnect_delay_sec", 1.0)
        )
        self.user_fps = target_fps or src_cfg.get("replay_fps")

        # State tracking
        self.cap: Optional[cv2.VideoCapture] = None
        self.fps: float = 25.0
        self.width: int = 0
        self.height: int = 0
        self.total_frames: int = 0
        self.frame_index: int = 0
        self.loop_count: int = 0
        self.is_connected: bool = False
        self.status: str = "initialized"
        self._last_frame_time: float = 0.0

    def open(self) -> "VideoSource":
        """Opens the capture source according to the selected mode."""
        self.status = "connecting"

        if self.mode in ("file", "replay"):
            video_path = path(self.source) if not Path(self.source).is_absolute() else Path(self.source)
            if not video_path.exists():
                self.status = "error"
                raise FileNotFoundError(f"Video file not found: {video_path}")

            self.cap = cv2.VideoCapture(str(video_path))
            if not self.cap.isOpened():
                self.status = "error"
                raise RuntimeError(f"Could not open video file: {video_path}")

            native_fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.fps = float(self.user_fps) if self.user_fps else (native_fps if native_fps and native_fps > 0 else 25.0)
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.is_connected = True
            self.status = "connected"
            logger.info("Opened %s source '%s' (%dx%d @ %.1f FPS, %d frames)",
                        self.mode, video_path, self.width, self.height, self.fps, self.total_frames)

        elif self.mode == "webcam":
            try:
                device_idx = int(self.source)
            except (ValueError, TypeError):
                device_idx = 0

            logger.info("Attempting to open webcam (device index %d)...", device_idx)
            self.cap = cv2.VideoCapture(device_idx)
            if not self.cap.isOpened():
                if self.cap is not None:
                    self.cap.release()
                self.cap = None
                self.status = "disconnected"
                raise RuntimeError(
                    f"Could not open local camera (device index {device_idx}). "
                    f"Please verify device connection, drivers, and OS camera permissions."
                )

            native_fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.fps = float(self.user_fps) if self.user_fps else (native_fps if native_fps and native_fps > 0 else 30.0)
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.is_connected = True
            self.status = "connected"
            logger.info("Webcam index %d opened successfully (%dx%d @ %.1f FPS)",
                        device_idx, self.width, self.height, self.fps)

        elif self.mode == "rtsp":
            rtsp_url = str(self.source).strip()
            logger.info("Attempting to connect to RTSP/IP-Camera stream: %s...", rtsp_url)
            self.cap = cv2.VideoCapture(rtsp_url)
            if not self.cap.isOpened():
                if self.cap is not None:
                    self.cap.release()
                self.cap = None
                self.status = "disconnected"
                raise RuntimeError(
                    f"Could not connect to RTSP stream: '{rtsp_url}'. "
                    f"Please check the stream URL, network connectivity, and RTSP server status."
                )

            native_fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.fps = float(self.user_fps) if self.user_fps else (native_fps if native_fps and native_fps > 0 else 25.0)
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.is_connected = True
            self.status = "connected"
            logger.info("RTSP stream connected (%dx%d @ %.1f FPS)", self.width, self.height, self.fps)

        elif self.mode == "windy":
            windy_cfg = self.cfg.get("windy", {})
            api_key = windy_cfg.get("api_key", "cgKO8KDfevVavn7lCPPudl806NicPOPC")
            webcam_id = str(self.source or windy_cfg.get("webcam_id", "1793889300")).strip()
            stream_url = windy_cfg.get("stream_url", "https://s5.webcamromania.ro/tljurilovca/index.m3u8")
            # If the user passed a full URL directly
            if self.source and (self.source.startswith("http://") or self.source.startswith("https://")):
                stream_url = self.source

            logger.info("Connecting to Windy Live Webcam #%s: %s...", webcam_id, stream_url)
            urls_to_try = [stream_url]
            if "index.m3u8" in stream_url:
                urls_to_try.append(stream_url.replace("index.m3u8", "tracks-v1a1/mono.m3u8"))

            self.cap = None
            for candidate_url in urls_to_try:
                for attempt in range(1, 4):
                    logger.debug("Opening stream attempt %d for %s", attempt, candidate_url)
                    self.cap = cv2.VideoCapture(candidate_url)
                    if self.cap.isOpened():
                        break
                    if self.cap is not None:
                        self.cap.release()
                    time.sleep(1.0)
                if self.cap is not None and self.cap.isOpened():
                    break

            if self.cap is None or not self.cap.isOpened():
                if self.cap is not None:
                    self.cap.release()
                self.cap = None
                self.status = "disconnected"
                raise RuntimeError(
                    f"Could not connect to Windy webcam stream (#{webcam_id}: {stream_url}). "
                    f"Please verify internet connection and stream availability."
                )

            native_fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.fps = float(self.user_fps) if self.user_fps else (native_fps if native_fps and native_fps > 0 else 25.0)
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.is_connected = True
            self.status = "connected"
            logger.info("Windy live webcam #%s connected successfully (%dx%d @ %.1f FPS)",
                        webcam_id, self.width, self.height, self.fps)

        self._last_frame_time = time.time()
        return self

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray], bool]:
        """Reads the next frame.

        Returns:
            (ok, frame, loop_flag):
            - ok: True if a valid frame was read.
            - frame: BGR image numpy array, or None.
            - loop_flag: True if a replay loop to beginning occurred on this read.
        """
        if self.cap is None or not self.cap.isOpened():
            return False, None, False

        # Real-time pacing for replay mode
        if self.mode == "replay" and self.fps > 0:
            target_interval = 1.0 / self.fps
            now = time.time()
            elapsed = now - self._last_frame_time
            if elapsed < target_interval:
                time.sleep(target_interval - elapsed)
            self._last_frame_time = time.time()

        ret, frame = self.cap.read()
        loop_occurred = False

        if not ret:
            if self.mode == "replay":
                # End of file reached -> seek back to frame 0 and continue seamlessly
                self.loop_count += 1
                logger.info("Replay reached EOF. Looping to start (Loop #%d)...", self.loop_count)
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret:
                    # If seek failed on codec, reopen the video capture cleanly
                    logger.warning("Video seek failed, reopening capture...")
                    self.cap.release()
                    video_path = path(self.source) if not Path(self.source).is_absolute() else Path(self.source)
                    self.cap = cv2.VideoCapture(str(video_path))
                    ret, frame = self.cap.read()
                loop_occurred = True
            elif self.mode in ("webcam", "rtsp", "windy"):
                # Real camera dropped a frame -> attempt reconnection
                logger.warning("Frame read failed from %s. Attempting reconnection...", self.mode)
                ret, frame = self._attempt_reconnect()
            else:
                # Mode == 'file' -> normal EOF
                self.is_connected = False
                self.status = "eof"
                return False, None, False

        if ret and frame is not None:
            self.frame_index += 1
            return True, frame, loop_occurred

        return False, None, False

    def _attempt_reconnect(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Handles camera stream reconnection with backoff delays."""
        self.status = "reconnecting"
        for attempt in range(1, self.reconnect_attempts + 1):
            logger.info("Reconnection attempt %d/%d in %.1fs...",
                        attempt, self.reconnect_attempts, self.reconnect_delay_sec)
            time.sleep(self.reconnect_delay_sec)
            try:
                if self.cap is not None:
                    self.cap.release()

                if self.mode == "webcam":
                    target = int(self.source)
                elif self.mode == "windy":
                    target = self.cfg.get("windy", {}).get("stream_url", "https://s5.webcamromania.ro/tljurilovca/index.m3u8")
                else:
                    target = str(self.source)
                self.cap = cv2.VideoCapture(target)
                if self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        logger.info("Reconnection successful on attempt %d!", attempt)
                        self.status = "connected"
                        self.is_connected = True
                        return True, frame
            except Exception as e:
                logger.warning("Reconnection attempt %d failed: %s", attempt, e)

        self.status = "disconnected"
        self.is_connected = False
        logger.error("Failed to reconnect to %s after %d attempts.", self.mode, self.reconnect_attempts)
        return False, None

    def release(self) -> None:
        """Releases the underlying capture device and resets status."""
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        self.is_connected = False
        self.status = "closed"
        logger.info("Capture source released.")

    def __enter__(self) -> "VideoSource":
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()
