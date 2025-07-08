#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "openai",
#     "python-dotenv",
# ]
# ///

import os
import sys
import asyncio
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv


async def main():
    """
    Fixed OpenAI TTS Script for macOS
    
    This script avoids the white noise issue by:
    1. Generating the audio file first
    2. Saving it to disk
    3. Playing it with the system audio player (afplay on macOS)
    
    Usage:
    - ./openai_tts_fixed.py                    # Uses default text
    - ./openai_tts_fixed.py "Your custom text" # Uses provided text
    - ./openai_tts_fixed.py --save-only "Text" # Only saves, doesn't play
    """
    
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    save_only = False
    args = sys.argv[1:]
    if "--save-only" in args:
        save_only = True
        args.remove("--save-only")
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please add your OpenAI API key to .env file:")
        print("OPENAI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    try:
        from openai import AsyncOpenAI
        
        # Initialize OpenAI client
        openai = AsyncOpenAI(api_key=api_key)
        
        print("🎙️  OpenAI TTS (Fixed)")
        print("=" * 25)
        
        # Get text from command line argument or use default
        if args:
            text = " ".join(args)
        else:
            text = "Today is a wonderful day to build something people love!"
        
        print(f"🎯 Text: {text}")
        print("🔊 Generating audio...")
        
        try:
            # Generate audio using OpenAI TTS
            response = await openai.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="ash",
                input=text,
                instructions="Speak in a cheerful, positive yet professional tone.",
                response_format="mp3",
            )
            
            # Create directory for permanent saves if requested
            if save_only:
                audio_dir = Path.cwd() / "logs" / "tts_audio"
                audio_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                audio_file = audio_dir / f"tts_{timestamp}.mp3"
            else:
                # Use temporary file for playback
                temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                audio_file = Path(temp_file.name)
                temp_file.close()
            
            # Save audio content
            audio_content = response.read()
            with open(audio_file, "wb") as f:
                f.write(audio_content)
            
            print(f"💾 Audio saved: {audio_file}")
            
            if not save_only:
                # Detect platform and use appropriate player
                import platform
                system = platform.system().lower()
                
                if system == "darwin":  # macOS
                    player_cmd = ["afplay", str(audio_file)]
                elif system == "linux":
                    # Try multiple players in order of preference
                    for player in ["aplay", "play", "mpg123", "ffplay"]:
                        if subprocess.run(["which", player], capture_output=True).returncode == 0:
                            if player == "aplay":
                                player_cmd = ["aplay", str(audio_file)]
                            else:
                                player_cmd = [player, str(audio_file)]
                            break
                    else:
                        print("❌ No suitable audio player found on Linux")
                        sys.exit(1)
                elif system == "windows":
                    # Use Windows Media Player
                    player_cmd = ["powershell", "-c", f"(New-Object Media.SoundPlayer '{audio_file}').PlaySync()"]
                else:
                    print(f"❌ Unsupported platform: {system}")
                    sys.exit(1)
                
                print(f"🔊 Playing with: {player_cmd[0]}")
                
                # Play the audio file
                result = subprocess.run(player_cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Playback complete!")
                    # Clean up temp file
                    try:
                        os.unlink(audio_file)
                    except:
                        pass
                else:
                    print(f"❌ Playback error: {result.stderr}")
                    sys.exit(1)
            else:
                print("✅ Audio saved successfully (playback skipped)")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            # More detailed error info
            if hasattr(e, 'response'):
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            sys.exit(1)
            
    except ImportError as e:
        print("❌ Error: Required package not installed")
        print("This script uses UV to auto-install dependencies.")
        print(f"Details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
