#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
# ]
# ///

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


def get_tts_script_path():
    """
    Use fixed OpenAI TTS script that avoids LocalAudioPlayer white noise issue
    """
    # Use absolute path to global hooks directory
    tts_dir = Path.home() / ".claude" / "hooks" / "utils" / "tts"
    
    # Use the fixed OpenAI TTS script
    fixed_script = tts_dir / "openai_tts_fixed.py"
    if fixed_script.exists():
        return str(fixed_script)
    
    # Fallback to original if fixed doesn't exist
    openai_script = tts_dir / "openai_tts.py"
    if openai_script.exists():
        return str(openai_script)
    
    return None


def announce_subagent_completion(input_data: dict):
    """Announce subagent completion using the best available TTS service with intelligent summaries."""
    try:
        tts_script = get_tts_script_path()
        if not tts_script:
            return  # No TTS scripts available
        
        # Get intelligent subagent completion message
        completion_message = get_intelligent_subagent_message(input_data)
        
        # Call the TTS script with the completion message
        subprocess.run([
            "uv", "run", tts_script, completion_message
        ], 
        capture_output=True,  # Suppress output
        timeout=10  # 10-second timeout
        )
        
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        # Fail silently if TTS encounters issues
        pass
    except Exception:
        # Fail silently for any other errors
        pass


def get_intelligent_subagent_message(input_data: dict):
    """
    Generate intelligent subagent completion message based on session transcript analysis.
    Falls back to generic messages if analysis fails.
    
    Args:
        input_data: Hook input data containing transcript_path
    
    Returns:
        str: Context-aware subagent completion message
    """
    try:
        # Try intelligent summary first
        transcript_path = input_data.get('transcript_path')
        if transcript_path and os.path.exists(transcript_path):
            utils_dir = Path.home() / ".claude" / "hooks" / "utils"
            
            # Import and use our transcript analysis system
            sys.path.insert(0, str(utils_dir))
            from transcript_analyzer import TranscriptAnalyzer
            from summary_generator import SummaryGenerator
            
            # Analyze transcript and generate summary
            analyzer = TranscriptAnalyzer()
            analysis = analyzer.analyze_transcript(transcript_path)
            
            generator = SummaryGenerator()
            summary = generator.generate_subagent_summary(analysis)
            
            # Return the intelligent summary
            return summary
    except Exception:
        # Fallback to original approach on any error
        pass
    
    # Fallback to generic message
    return "Subagent Complete"


def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--chat', action='store_true', help='Copy transcript to chat.json')
        args = parser.parse_args()
        
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        # Extract required fields
        session_id = input_data.get("session_id", "")
        stop_hook_active = input_data.get("stop_hook_active", False)

        # Ensure log directory exists
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "subagent_stop.json")

        # Read existing log data or initialize empty list
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []
        
        # Append new data
        log_data.append(input_data)
        
        # Write back to file with formatting
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        # Handle --chat switch (same as stop.py)
        if args.chat and 'transcript_path' in input_data:
            transcript_path = input_data['transcript_path']
            if os.path.exists(transcript_path):
                # Read .jsonl file and convert to JSON array
                chat_data = []
                try:
                    with open(transcript_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    chat_data.append(json.loads(line))
                                except json.JSONDecodeError:
                                    pass  # Skip invalid lines
                    
                    # Write to logs/chat.json
                    chat_file = os.path.join(log_dir, 'chat.json')
                    with open(chat_file, 'w') as f:
                        json.dump(chat_data, f, indent=2)
                except Exception:
                    pass  # Fail silently

        # Announce subagent completion via TTS with intelligent summary
        announce_subagent_completion(input_data)

        sys.exit(0)

    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)


if __name__ == "__main__":
    main()