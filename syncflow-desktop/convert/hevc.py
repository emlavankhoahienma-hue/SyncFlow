import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger("syncflow.convert.hevc")

def convert_hevc_to_mp4(input_path: Path, output_path: Optional[Path] = None) -> Tuple[bool, Path, str]:
    """
    Converts HEVC/QuickTime .mov video to MP4 (H.264, CRF 18 visually lossless, AAC 256k).
    Invokes ffmpeg CLI.
    """
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        msg = "ffmpeg not found in PATH. Keeping original file format."
        logger.warning(msg)
        return False, input_path, msg

    if output_path is None:
        output_path = input_path.with_suffix(".mp4")

    # Command: ffmpeg -y -i in.mov -c:v libx264 -crf 18 -preset slow -c:a aac -b:a 256k out.mp4
    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", str(input_path),
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "slow",
        "-c:a", "aac",
        "-b:a", "256k",
        "-movflags", "+faststart",
        str(output_path)
    ]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=1800  # 30 min max for large video
        )
        if proc.returncode == 0 and output_path.exists():
            logger.info(f"Video converted successfully: {output_path}")
            return True, output_path, "Conversion succeeded"
        else:
            err = proc.stderr[-500:] if proc.stderr else "Unknown error"
            logger.error(f"ffmpeg conversion failed: {err}")
            return False, input_path, f"ffmpeg error: {err}"
    except Exception as e:
        logger.error(f"ffmpeg execution error: {e}")
        return False, input_path, str(e)
