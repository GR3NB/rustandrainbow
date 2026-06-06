#!/usr/bin/env python3
"""
Creates a simple branded test video for TikTok demo recording.
Outputs: output/tiktok_demo_test.mp4  (~10 seconds, 1080x1920 vertical)

Usage:
    python3 create_test_video.py

Requirements:
    pip3 install moviepy pillow
"""

import os
import sys
import tempfile
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_PATH = str(OUTPUT_DIR / "tiktok_demo_test.mp4")


def make_frame(text_lines, bg_color, text_color, size=(1080, 1920), fontsize=80):
    """Create a PIL image with centered text."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", size, bg_color)
    draw = ImageDraw.Draw(img)

    # Use default font (always available)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", fontsize)
    except Exception:
        font = ImageFont.load_default()

    # Calculate total text block height
    line_height = fontsize + 20
    total_height = line_height * len(text_lines)
    y_start = (size[1] - total_height) // 2

    for i, line in enumerate(text_lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (size[0] - text_w) // 2
        y = y_start + i * line_height
        draw.text((x, y), line, fill=text_color, font=font)

    return img


def create_video():
    try:
        from PIL import Image
        import moviepy
    except ImportError:
        print("[ERROR] Missing dependencies. Run:")
        print("  pip3 install moviepy pillow")
        sys.exit(1)

    # moviepy 2.x import style
    try:
        from moviepy import ImageClip, concatenate_videoclips
    except ImportError:
        try:
            from moviepy.editor import ImageClip, concatenate_videoclips
        except ImportError:
            print("[ERROR] Could not import moviepy. Run: pip3 install moviepy")
            sys.exit(1)

    print("Creating branded test video for TikTok demo...")

    RUST  = (181, 69, 27)
    CREAM = (245, 240, 232)

    slides = [
        {"lines": ["Rust & Rainbow"],       "bg": CREAM, "fg": RUST,  "duration": 3},
        {"lines": ["Vizsla apparel",
                   "for gay dog owners"],    "bg": RUST,  "fg": CREAM, "duration": 3},
        {"lines": ["TikTok Integration",
                   "Demo Upload"],           "bg": CREAM, "fg": RUST,  "duration": 4},
    ]

    clips = []
    tmp_files = []

    for i, slide in enumerate(slides):
        img = make_frame(slide["lines"], slide["bg"], slide["fg"])
        tmp_path = f"/tmp/rr_slide_{i}.png"
        img.save(tmp_path)
        tmp_files.append(tmp_path)

        # moviepy 2.x uses with_duration; fall back to set_duration for 1.x
        clip = ImageClip(tmp_path)
        try:
            clip = clip.with_duration(slide["duration"])
        except AttributeError:
            clip = clip.set_duration(slide["duration"])

        clips.append(clip)

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        OUTPUT_PATH,
        fps=24,
        codec="libx264",
        audio=False,
        logger=None,
    )

    # Cleanup temp files
    for f in tmp_files:
        try:
            os.remove(f)
        except Exception:
            pass

    size_mb = os.path.getsize(OUTPUT_PATH) / 1_000_000
    print(f"\n✓ Test video created: {OUTPUT_PATH}")
    print(f"  Duration: ~10 seconds")
    print(f"  Size: {size_mb:.1f} MB")
    print(f"\nRun next: python3 demo_tiktok.py")


if __name__ == "__main__":
    create_video()
