#!/usr/bin/env python3
"""
Script to speed up audio files by specified percentages.
Requires: pip install pydub
"""

import os
import sys

from pydub import AudioSegment


def speed_up_audio(input_file, speed_factor, output_file=None):
    """
    Speed up an audio file by a given factor.

    Args:
        input_file: Path to input audio file
        speed_factor: Speed multiplier (e.g., 1.25 for 25% faster, 1.5 for 50% faster)
        output_file: Path for output file (optional, auto-generated if not provided)
    """
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        return False

    # Generate output filename if not provided
    if output_file is None:
        base_name = os.path.splitext(input_file)[0]
        extension = os.path.splitext(input_file)[1]
        speed_percent = int((speed_factor - 1) * 100)
        output_file = f"{base_name}_speed_{speed_percent}pct{extension}"

    try:
        # Load audio file
        print(f"Loading audio file: {input_file}")
        audio = AudioSegment.from_file(input_file)

        # Calculate new frame rate for speed change
        original_frame_rate = audio.frame_rate
        new_frame_rate = int(original_frame_rate * speed_factor)

        # Change the frame rate to speed up/slow down
        sped_up_audio = audio._spawn(
            audio.raw_data, overrides={"frame_rate": new_frame_rate}
        )

        # Set the frame rate back to original for proper playback
        sped_up_audio = sped_up_audio.set_frame_rate(original_frame_rate)

        # Export the sped up audio
        print(f"Saving sped up audio to: {output_file}")
        sped_up_audio.export(output_file, format=os.path.splitext(output_file)[1][1:])

        # Calculate duration change
        original_duration = len(audio) / 1000.0  # in seconds
        new_duration = len(sped_up_audio) / 1000.0  # in seconds
        print(f"Original duration: {original_duration:.1f}s")
        print(f"New duration: {new_duration:.1f}s")
        print(
            f"Speed factor: {speed_factor}x ({int((speed_factor - 1) * 100)}% faster)"
        )

        return True

    except Exception as e:
        print(f"Error processing audio file: {e}")
        return False


def main():
    """Main function to process command line arguments."""
    if len(sys.argv) < 2:
        print(
            "Usage: python speed_up_audio.py <input_file> "
            "[speed_percent1] [speed_percent2] ..."
        )
        print("Example: python speed_up_audio.py sound/reach-the-exit.mp3 25 50")
        print("If no speed percentages provided, creates 25% and 50% faster versions")
        sys.exit(1)

    input_file = sys.argv[1]

    # Default speed percentages if not provided
    speed_percentages = (
        [25, 50] if len(sys.argv) == 2 else [int(x) for x in sys.argv[2:]]
    )

    print(f"Processing audio file: {input_file}")

    for speed_pct in speed_percentages:
        speed_factor = 1.0 + (speed_pct / 100.0)
        print(f"\nCreating {speed_pct}% faster version...")
        success = speed_up_audio(input_file, speed_factor)

        if success:
            print(f"✓ Successfully created {speed_pct}% faster version")
        else:
            print(f"✗ Failed to create {speed_pct}% faster version")

    print("\nDone!")


if __name__ == "__main__":
    main()
