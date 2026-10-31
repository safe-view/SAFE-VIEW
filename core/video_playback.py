"""브라우저에서 재생 가능한 H.264 영상 변환과 캐시를 제공한다."""

from __future__ import annotations

import os
import re
import subprocess


def get_playable_video(
    clip_path: str,
    cache_dir: str,
    timeout_sec: float = 30.0,
) -> str | None:
    filename = os.path.basename(clip_path)
    os.makedirs(cache_dir, exist_ok=True)
    converted_path = os.path.join(cache_dir, filename)
    if os.path.exists(converted_path):
        return converted_path
    try:
        from imageio_ffmpeg import get_ffmpeg_exe

        ffmpeg = get_ffmpeg_exe()
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                clip_path,
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
                "-movflags",
                "+faststart",
                "-an",
                converted_path,
            ],
            capture_output=True,
            timeout=timeout_sec,
        )
        return converted_path if os.path.exists(converted_path) else None
    except Exception:
        return None


def get_video_duration_seconds(path: str) -> float | None:
    try:
        from imageio_ffmpeg import get_ffmpeg_exe

        result = subprocess.run(
            [get_ffmpeg_exe(), "-i", path],
            capture_output=True,
            timeout=30.0,
        )
    except Exception:
        return None

    match = re.search(
        rb"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)",
        result.stderr,
    )
    if not match:
        return None

    hours, minutes, seconds = (part.decode("ascii") for part in match.groups())
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
