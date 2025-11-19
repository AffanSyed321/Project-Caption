import cv2
from moviepy.editor import VideoFileClip
import os
from typing import List
import tempfile


class VideoService:
    """Service for processing and extracting frames from videos"""

    def __init__(self):
        self.frame_interval = 2  # Extract 1 frame every 2 seconds

    def extract_key_frames(self, video_path: str, max_frames: int = 5) -> List[str]:
        """
        Extract key frames from video for analysis
        Returns list of paths to extracted frame images
        """
        frame_paths = []

        try:
            # Load video
            video = cv2.VideoCapture(video_path)
            fps = video.get(cv2.CAP_PROP_FPS)
            total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0

            # Calculate frame interval to get max_frames evenly distributed
            if duration > 0:
                interval = max(1, int((duration / max_frames) * fps))
            else:
                interval = 1

            frame_count = 0
            extracted_count = 0

            while extracted_count < max_frames:
                ret, frame = video.read()

                if not ret:
                    break

                # Extract frame at intervals
                if frame_count % interval == 0:
                    # Save frame to temp file
                    temp_frame = tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix='.jpg',
                        dir=tempfile.gettempdir()
                    )
                    frame_path = temp_frame.name
                    temp_frame.close()

                    cv2.imwrite(frame_path, frame)
                    frame_paths.append(frame_path)
                    extracted_count += 1

                frame_count += 1

            video.release()

        except Exception as e:
            print(f"Error extracting frames: {str(e)}")
            # Clean up any extracted frames on error
            for path in frame_paths:
                if os.path.exists(path):
                    os.remove(path)
            raise

        return frame_paths

    def get_video_info(self, video_path: str) -> dict:
        """Get video metadata"""
        try:
            clip = VideoFileClip(video_path)
            info = {
                "duration": clip.duration,
                "fps": clip.fps,
                "size": clip.size,
                "has_audio": clip.audio is not None
            }
            clip.close()
            return info
        except Exception as e:
            return {
                "error": str(e),
                "duration": 0,
                "fps": 0,
                "size": (0, 0),
                "has_audio": False
            }

    def cleanup_frames(self, frame_paths: List[str]):
        """Clean up temporary frame files"""
        for path in frame_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"Error cleaning up frame {path}: {str(e)}")

    def is_video_file(self, filename: str) -> bool:
        """Check if file is a video"""
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv']
        return any(filename.lower().endswith(ext) for ext in video_extensions)
