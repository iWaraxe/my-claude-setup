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
import random
from pathlib import Path

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


def announce_notification(input_data: dict):
    """Announce that the agent needs user input with intelligent context."""
    try:
        tts_script = get_tts_script_path()
        if not tts_script:
            return  # No TTS scripts available
        
        # Try to get intelligent notification message
        notification_message = get_intelligent_notification_message(input_data)
        
        # Call the TTS script with the notification message
        subprocess.run([
            "uv", "run", tts_script, notification_message
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


def get_intelligent_notification_message(input_data: dict):
    """
    Generate intelligent notification message based on current session context.
    Falls back to generic messages if analysis fails.
    
    Args:
        input_data: Hook input data containing session information
    
    Returns:
        str: Context-aware notification message
    """
    try:
        # Find the most recent transcript for this session
        transcript_path = find_current_transcript()
        if transcript_path and os.path.exists(transcript_path):
            utils_dir = Path.home() / ".claude" / "hooks" / "utils"
            
            # Import and use our transcript analysis system
            sys.path.insert(0, str(utils_dir))
            from transcript_analyzer import TranscriptAnalyzer
            from summary_generator import SummaryGenerator
            
            # Analyze transcript and generate context-aware notification
            analyzer = TranscriptAnalyzer()
            analysis = analyzer.analyze_transcript(transcript_path)
            
            generator = SummaryGenerator()
            notification = generator.generate_notification_summary(analysis)
            
            return notification
    except Exception:
        # Fallback to original approach on any error
        pass
    
    # Fallback to original generic notification
    return get_generic_notification_message()


def find_current_transcript():
    """Find the most recent transcript file for the current session."""
    try:
        # Look in the standard Claude projects directory
        projects_dir = Path.home() / ".claude" / "projects"
        if not projects_dir.exists():
            return None
        
        # Find the most recent .jsonl file
        jsonl_files = list(projects_dir.glob("*/*.jsonl"))
        if not jsonl_files:
            return None
        
        # Return the most recently modified file
        most_recent = max(jsonl_files, key=lambda f: f.stat().st_mtime)
        return str(most_recent)
    except Exception:
        return None


def get_generic_notification_message():
    """Generate a generic notification message as fallback."""
    # Get engineer name if available
    engineer_name = os.getenv('ENGINEER_NAME', '').strip()
    
    # Create notification message with 30% chance to include name
    if engineer_name and random.random() < 0.3:
        return f"{engineer_name}, your agent needs your input"
    else:
        return "Your agent needs your input"


def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--notify', action='store_true', help='Enable TTS notifications')
        args = parser.parse_args()
        
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())
        
        # Ensure log directory exists
        import os
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'notification.json')
        
        # Read existing log data or initialize empty list
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []
        
        # Append new data
        log_data.append(input_data)
        
        # Write back to file with formatting
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        # Announce notification via TTS only if --notify flag is set
        # Skip TTS for the generic "Claude is waiting for your input" message
        if args.notify and input_data.get('message') != 'Claude is waiting for your input':
            announce_notification(input_data)
        
        sys.exit(0)
        
    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)

if __name__ == '__main__':
    main()