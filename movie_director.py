"""
Movie Director Module
Creates recap videos by combining manga panels with narration audio.
Adds transitions, effects, and timing synchronization.
"""

import os
import cv2
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont

try:
    from moviepy.editor import (
        ImageClip, AudioFileClip, concatenate_videoclips,
        CompositeVideoClip, concatenate_audioclips, ColorClip
    )
    from moviepy.video.fx.all import fadein, fadeout
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logging.warning("moviepy not installed. Video creation will use OpenCV fallback.")

logger = logging.getLogger(__name__)


@dataclass
class VideoConfig:
    """Configuration for video generation."""
    width: int = 1280
    height: int = 720
    fps: int = 24
    transition_duration: float = 0.5
    panel_display_duration: float = 4.0  # seconds per panel
    background_color: Tuple[int, int, int] = (20, 20, 25)
    text_overlay: bool = True
    ken_burns: bool = True  # Slow zoom/pan effect
    output_format: str = "mp4"
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    bitrate: str = "5000k"


class MovieDirector:
    """Creates recap videos from manga panels and narration."""

    def __init__(self, config: Optional[VideoConfig] = None):
        self.config = config or VideoConfig()
        self.transition_effects = {
            'fade': self._fade_transition,
            'slide_left': self._slide_left_transition,
            'slide_right': self._slide_right_transition,
            'zoom': self._zoom_transition,
            'wipe': self._wipe_transition,
        }

    def create_recap_video(
        self,
        panel_paths: List[str],
        narration_audio_path: str,
        output_path: str,
        title: str = "",
        chapter_titles: Optional[List[str]] = None,
        transition_type: str = "fade",
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> str:
        """
        Create a recap video from panels and narration.

        Args:
            panel_paths: List of panel image paths
            narration_audio_path: Path to narration audio file
            output_path: Output video path
            title: Video title (shown as overlay)
            chapter_titles: Optional chapter titles for panels
            transition_type: Transition effect name
            progress_callback: Progress callback

        Returns:
            Path to generated video
        """
        if not panel_paths:
            raise ValueError("No panels provided for video")

        if not os.path.exists(narration_audio_path):
            raise FileNotFoundError(f"Narration audio not found: {narration_audio_path}")

        logger.info(f"Creating recap video with {len(panel_paths)} panels")

        if MOVIEPY_AVAILABLE:
            return self._create_with_moviepy(
                panel_paths, narration_audio_path, output_path,
                title, chapter_titles, transition_type, progress_callback
            )
        else:
            return self._create_with_opencv(
                panel_paths, narration_audio_path, output_path,
                title, chapter_titles, progress_callback
            )

    def _create_with_moviepy(
        self,
        panel_paths: List[str],
        narration_audio_path: str,
        output_path: str,
        title: str,
        chapter_titles: Optional[List[str]],
        transition_type: str,
        progress_callback: Optional[Callable[[str, int], None]]
    ) -> str:
        """Create video using MoviePy (higher quality)."""
        try:
            # Load narration audio to get duration
            narration = AudioFileClip(narration_audio_path)
            total_audio_duration = narration.duration

            # Calculate display duration per panel
            num_panels = len(panel_paths)
            panel_duration = total_audio_duration / num_panels if num_panels > 0 else 4.0

            # Create video clips for each panel
            clips = []
            transition = self.config.transition_duration

            for i, panel_path in enumerate(panel_paths):
                if progress_callback:
                    progress_callback(f"Processing panel {i+1}/{num_panels}", int((i+1)/num_panels*50))

                # Load and resize panel
                img = Image.open(panel_path).convert('RGB')
                img = self._fit_to_resolution(img, self.config.width, self.config.height)

                # Create image clip
                img_array = np.array(img)
                clip = ImageClip(img_array, duration=panel_duration)

                # Apply Ken Burns effect (slow zoom)
                if self.config.ken_burns:
                    clip = self._apply_ken_burns(clip)

                # Add text overlay
                if self.config.text_overlay and chapter_titles and i < len(chapter_titles):
                    clip = self._add_text_overlay(clip, chapter_titles[i])

                # Apply fade transitions
                clip = fadein(clip, transition)
                clip = fadeout(clip, transition)

                clips.append(clip)

            # Concatenate all clips
            if progress_callback:
                progress_callback("Concatenating video clips...", 60)

            video = concatenate_videoclips(clips, method="compose")

            # Set narration audio
            if progress_callback:
                progress_callback("Adding narration audio...", 75)

            # Adjust video duration to match audio
            if video.duration > total_audio_duration:
                video = video.subclip(0, total_audio_duration)

            video = video.set_audio(narration)

            # Add title card at beginning
            if title:
                title_card = self._create_title_card(title, narration.duration)
                video = concatenate_videoclips([title_card, video], method="compose")

            # Write output
            if progress_callback:
                progress_callback("Rendering final video...", 85)

            output_path = str(output_path)
            video.write_videofile(
                output_path,
                fps=self.config.fps,
                codec=self.config.video_codec,
                audio_codec=self.config.audio_codec,
                bitrate=self.config.bitrate,
                threads=4,
                logger=None  # Suppress moviepy console output
            )

            # Clean up
            video.close()
            narration.close()
            for clip in clips:
                clip.close()

            if progress_callback:
                progress_callback("Video complete!", 100)

            logger.info(f"Video created: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"MoviePy video creation failed: {e}")
            # Fall back to OpenCV
            return self._create_with_opencv(
                panel_paths, narration_audio_path, output_path,
                title, chapter_titles, progress_callback
            )

    def _create_with_opencv(
        self,
        panel_paths: List[str],
        narration_audio_path: str,
        output_path: str,
        title: str,
        chapter_titles: Optional[List[str]],
        progress_callback: Optional[Callable[[str, int], None]]
    ) -> str:
        """Create video using OpenCV (fallback method)."""
        try:
            import soundfile as sf
            audio_data, audio_samplerate = sf.read(narration_audio_path)
            total_audio_duration = len(audio_data) / audio_samplerate
        except Exception:
            # Estimate duration
            total_audio_duration = len(panel_paths) * 4.0

        # Calculate frames per panel
        num_panels = len(panel_paths)
        frames_per_panel = int((total_audio_duration / num_panels) * self.config.fps)
        total_frames = frames_per_panel * num_panels

        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, self.config.fps,
                                 (self.config.width, self.config.height))

        if not writer.isOpened():
            raise RuntimeError("Could not open video writer")

        frame_count = 0

        # Add title card (2 seconds)
        if title:
            title_frames = 2 * self.config.fps
            title_img = self._create_title_image(title)
            for _ in range(title_frames):
                writer.write(title_img)
                frame_count += 1

        # Process each panel
        for i, panel_path in enumerate(panel_paths):
            if progress_callback:
                progress = 50 + int((i + 1) / num_panels * 50)
                progress_callback(f"Rendering panel {i+1}/{num_panels}", progress)

            # Load and resize panel
            img = cv2.imread(panel_path)
            if img is None:
                # Create blank frame if image can't be loaded
                img = np.full((self.config.height, self.config.width, 3),
                              self.config.background_color, dtype=np.uint8)
            else:
                img = self._fit_to_resolution_cv2(img, self.config.width, self.config.height)

            # Add chapter title overlay
            if chapter_titles and i < len(chapter_titles):
                img = self._add_text_overlay_cv2(img, chapter_titles[i])

            # Write frames for this panel
            for _ in range(frames_per_panel):
                writer.write(img)
                frame_count += 1

        writer.release()

        # Combine with audio using ffmpeg if available
        try:
            final_output = self._combine_audio_video(output_path, narration_audio_path)
            if progress_callback:
                progress_callback("Video complete!", 100)
            return final_output
        except Exception as e:
            logger.warning(f"Could not combine audio: {e}. Video saved without audio.")
            if progress_callback:
                progress_callback("Video complete (no audio)!", 100)
            return output_path

    def _fit_to_resolution(self, img: Image.Image, width: int, height: int) -> Image.Image:
        """Resize image to fit resolution while maintaining aspect ratio."""
        img_ratio = img.width / img.height
        target_ratio = width / height

        if img_ratio > target_ratio:
            # Image is wider - fit to width
            new_width = width
            new_height = int(width / img_ratio)
        else:
            # Image is taller - fit to height
            new_height = height
            new_width = int(height * img_ratio)

        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Create background and center the image
        background = Image.new('RGB', (width, height), self.config.background_color)
        x = (width - new_width) // 2
        y = (height - new_height) // 2
        background.paste(resized, (x, y))

        return background

    def _fit_to_resolution_cv2(self, img: np.ndarray, width: int, height: int) -> np.ndarray:
        """Resize OpenCV image to fit resolution."""
        h, w = img.shape[:2]
        img_ratio = w / h
        target_ratio = width / height

        if img_ratio > target_ratio:
            new_width = width
            new_height = int(width / img_ratio)
        else:
            new_height = height
            new_width = int(height * img_ratio)

        resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

        # Create background
        background = np.full((height, width, 3), self.config.background_color, dtype=np.uint8)
        x = (width - new_width) // 2
        y = (height - new_height) // 2
        background[y:y+new_height, x:x+new_width] = resized

        return background

    def _apply_ken_burns(self, clip):
        """Apply slow zoom/pan effect to a clip."""
        from moviepy.video.fx.all import resize

        def resize_func(t):
            # Slow zoom from 100% to 110%
            return 1.0 + (t / clip.duration) * 0.1

        return clip.fx(resize, newsize=resize_func)

    def _add_text_overlay(self, clip, text: str):
        """Add text overlay to a clip."""
        from moviepy.editor import TextClip

        txt_clip = TextClip(
            text,
            fontsize=24,
            color='white',
            font='Arial',
            stroke_color='black',
            stroke_width=1
        )
        txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(clip.duration)
        txt_clip = txt_clip.margin(bottom=20, opacity=0)

        return CompositeVideoClip([clip, txt_clip])

    def _add_text_overlay_cv2(self, img: np.ndarray, text: str) -> np.ndarray:
        """Add text overlay to OpenCV image."""
        h, w = img.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2

        # Calculate text size
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        text_x = (w - text_size[0]) // 2
        text_y = h - 30

        # Draw background rectangle
        overlay = img.copy()
        rect_x1 = max(0, text_x - 10)
        rect_y1 = text_y - text_size[1] - 10
        rect_x2 = min(w, text_x + text_size[0] + 10)
        rect_y2 = text_y + 10
        cv2.rectangle(overlay, (rect_x1, rect_y1), (rect_x2, rect_y2), (0, 0, 0), -1)
        img = cv2.addWeighted(overlay, 0.6, img, 0.4, 0)

        # Draw text
        cv2.putText(img, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness)

        return img

    def _create_title_image(self, title: str) -> np.ndarray:
        """Create a title card image using OpenCV."""
        img = np.full((self.config.height, self.config.width, 3),
                      self.config.background_color, dtype=np.uint8)

        font = cv2.FONT_HERSHEY_SIMPLEX

        # Draw decorative line
        line_y = self.config.height // 2 - 50
        cv2.line(img, (100, line_y), (self.config.width - 100, line_y), (200, 150, 100), 3)

        # Draw title
        font_scale = 1.5
        thickness = 3
        text_size = cv2.getTextSize(title, font, font_scale, thickness)[0]
        text_x = (self.config.width - text_size[0]) // 2
        text_y = self.config.height // 2
        cv2.putText(img, title, (text_x, text_y), font, font_scale, (255, 255, 255), thickness)

        # Draw subtitle
        subtitle = "Manga Recap"
        sub_font_scale = 0.8
        sub_thickness = 1
        sub_size = cv2.getTextSize(subtitle, font, sub_font_scale, sub_thickness)[0]
        sub_x = (self.config.width - sub_size[0]) // 2
        sub_y = self.config.height // 2 + 60
        cv2.putText(img, subtitle, (sub_x, sub_y), font, sub_font_scale, (180, 180, 180), sub_thickness)

        # Draw bottom line
        line_y2 = self.config.height // 2 + 100
        cv2.line(img, (100, line_y2), (self.config.width - 100, line_y2), (200, 150, 100), 3)

        return img

    def _create_title_card(self, title: str, duration: float):
        """Create a title card clip for MoviePy."""
        from moviepy.editor import TextClip, ColorClip, CompositeVideoClip

        # Background
        bg = ColorClip(
            size=(self.config.width, self.config.height),
            color=(self.config.background_color[0] / 255,
                   self.config.background_color[1] / 255,
                   self.config.background_color[2] / 255),
            duration=min(3.0, duration * 0.1)  # Title shows for 10% of duration or 3s
        )

        # Title text
        title_clip = TextClip(
            title,
            fontsize=48,
            color='white',
            font='Arial-Bold',
            stroke_color='black',
            stroke_width=2
        )
        title_clip = title_clip.set_position('center').set_duration(bg.duration)

        # Subtitle
        subtitle_clip = TextClip(
            "Manga Recap",
            fontsize=24,
            color='#cccccc',
            font='Arial'
        )
        subtitle_clip = subtitle_clip.set_position(('center', 0.6)).set_duration(bg.duration)

        # Fade in/out
        title_clip = fadein(title_clip, 0.5)
        title_clip = fadeout(title_clip, 0.5)
        subtitle_clip = fadein(subtitle_clip, 0.5)
        subtitle_clip = fadeout(subtitle_clip, 0.5)

        return CompositeVideoClip([bg, title_clip, subtitle_clip])

    def _combine_audio_video(self, video_path: str, audio_path: str) -> str:
        """Combine video and audio using ffmpeg."""
        import shutil

        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            raise RuntimeError("ffmpeg not found in PATH")

        output_path = video_path.replace('.mp4', '_final.mp4')

        import subprocess
        cmd = [
            ffmpeg_path, '-y',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr}")

        # Replace original with combined version
        os.replace(output_path, video_path)
        return video_path

    # Transition effects (stubs for extensibility)
    def _fade_transition(self, clip1, clip2):
        return fadeout(clip1, self.config.transition_duration), fadein(clip2, self.config.transition_duration)

    def _slide_left_transition(self, clip1, clip2):
        return clip1, clip2  # Implement if needed

    def _slide_right_transition(self, clip1, clip2):
        return clip1, clip2

    def _zoom_transition(self, clip1, clip2):
        return clip1, clip2

    def _wipe_transition(self, clip1, clip2):
        return clip1, clip2

    def estimate_video_duration(self, num_panels: int, narration_duration: Optional[float] = None) -> float:
        """Estimate final video duration."""
        if narration_duration:
            return narration_duration + 3.0  # Add title card time
        return num_panels * self.config.panel_display_duration + 3.0
