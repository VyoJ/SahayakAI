import os
import sys
import subprocess
import zipfile
import urllib.request
from pathlib import Path
from pydub import AudioSegment
import tempfile


class MP4ToMP3Converter:
    def __init__(self):
        self.ffmpeg_path = None
        self.setup_ffmpeg()

    def setup_ffmpeg(self):
        """Setup FFmpeg for Windows if not already available"""
        try:
            # Try to use system FFmpeg first
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            print("Using system FFmpeg")
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Check if we have a local FFmpeg
        local_ffmpeg = Path("./ffmpeg/bin/ffmpeg.exe")
        if local_ffmpeg.exists():
            self.ffmpeg_path = str(local_ffmpeg.parent)
            AudioSegment.converter = str(local_ffmpeg)
            AudioSegment.ffmpeg = str(local_ffmpeg)
            AudioSegment.ffprobe = str(local_ffmpeg.parent / "ffprobe.exe")
            print(f"Using local FFmpeg: {local_ffmpeg}")
            return

        print("FFmpeg not found. Please install FFmpeg manually:")
        print("1. Download from: https://www.gyan.dev/ffmpeg/builds/")
        print("2. Extract to './ffmpeg/' directory")
        print("3. Or install with: winget install Gyan.FFmpeg")

    def convert_single_file(self, input_file, output_file=None, bitrate="192k"):
        """
        Convert single MP4 file to MP3

        Args:
            input_file (str): Path to input MP4 file
            output_file (str): Path to output MP3 file
            bitrate (str): Audio bitrate

        Returns:
            bool: Success status
        """
        try:
            input_path = Path(input_file)

            if not input_path.exists():
                print(f"Error: File '{input_file}' not found")
                return False

            if output_file is None:
                output_file = input_path.with_suffix(".mp3")

            print(f"Converting: {input_file} -> {output_file}")

            # Load audio from MP4
            audio = AudioSegment.from_file(input_file, format="mp4")

            # Export as MP3
            audio.export(output_file, format="mp3", bitrate=bitrate)

            print(f"✓ Conversion successful: {output_file}")
            return True

        except Exception as e:
            print(f"✗ Error converting {input_file}: {str(e)}")
            return False

    def convert_batch(self, input_directory, output_directory=None, bitrate="192k"):
        """
        Convert all MP4 files in directory

        Args:
            input_directory (str): Input directory path
            output_directory (str): Output directory path
            bitrate (str): Audio bitrate
        """
        input_dir = Path(input_directory)

        if not input_dir.exists():
            print(f"Error: Directory '{input_directory}' not found")
            return

        if output_directory:
            output_dir = Path(output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = input_dir

        # Find MP4 files
        mp4_files = list(input_dir.glob("*.mp4")) + list(input_dir.glob("*.MP4"))

        if not mp4_files:
            print(f"No MP4 files found in '{input_directory}'")
            return

        print(f"Found {len(mp4_files)} MP4 files")

        successful = 0
        failed = 0

        for mp4_file in mp4_files:
            output_file = output_dir / f"{mp4_file.stem}.mp3"

            if self.convert_single_file(str(mp4_file), str(output_file), bitrate):
                successful += 1
            else:
                failed += 1

        print(f"\nBatch conversion complete:")
        print(f"  ✓ Successful: {successful}")
        print(f"  ✗ Failed: {failed}")


def install_ffmpeg_windows():
    """Helper function to install FFmpeg on Windows"""
    try:
        print("Attempting to install FFmpeg using winget...")
        result = subprocess.run(
            ["winget", "install", "Gyan.FFmpeg"], capture_output=True, text=True
        )
        if result.returncode == 0:
            print("✓ FFmpeg installed successfully!")
            return True
        else:
            print("winget installation failed")
            return False
    except FileNotFoundError:
        print("winget not available")
        return False


def main():
    """Main function"""
    converter = MP4ToMP3Converter()

    if len(sys.argv) < 2:
        print("MP4 to MP3 Converter (Windows Compatible)")
        print("\nUsage:")
        print(
            "  Single file: python mp4_to_mp3_windows.py <input.mp4> [output.mp3] [bitrate]"
        )
        print(
            "  Batch mode:  python mp4_to_mp3_windows.py --batch <input_dir> [output_dir] [bitrate]"
        )
        print("  Install FFmpeg: python mp4_to_mp3_windows.py --install-ffmpeg")
        print("\nExamples:")
        print("  python mp4_to_mp3_windows.py video.mp4")
        print("  python mp4_to_mp3_windows.py video.mp4 audio.mp3 128k")
        print("  python mp4_to_mp3_windows.py --batch ./videos")
        print("  python mp4_to_mp3_windows.py --batch ./videos ./audio 320k")
        return

    # Install FFmpeg
    if sys.argv[1] == "--install-ffmpeg":
        install_ffmpeg_windows()
        return

    # Batch conversion
    if sys.argv[1] == "--batch":
        if len(sys.argv) < 3:
            print("Error: Specify input directory for batch mode")
            return

        input_dir = sys.argv[2]
        output_dir = sys.argv[3] if len(sys.argv) > 3 else None
        bitrate = sys.argv[4] if len(sys.argv) > 4 else "192k"

        converter.convert_batch(input_dir, output_dir, bitrate)

    # Single file conversion
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        bitrate = sys.argv[3] if len(sys.argv) > 3 else "192k"

        converter.convert_single_file(input_file, output_file, bitrate)


if __name__ == "__main__":
    main()
