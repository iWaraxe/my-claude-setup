# Intelligent Summary Configuration

This document describes how to configure the intelligent summary features for Claude Code hooks.

## Environment Variables

You can control the behavior of intelligent summaries using these environment variables in your shell or `.env` file:

### CLAUDE_HOOKS_SUMMARY_ENABLED
**Default:** `true`  
**Values:** `true` | `false`

Enable or disable intelligent summary generation across all hooks.

```bash
# Enable intelligent summaries (default)
export CLAUDE_HOOKS_SUMMARY_ENABLED=true

# Disable intelligent summaries (fall back to generic messages)
export CLAUDE_HOOKS_SUMMARY_ENABLED=false
```

When disabled, hooks will use the original generic messages:
- Stop hook: "Work complete!", "All done!", etc.
- Notification hook: "Your agent needs your input"
- SubagentStop hook: "Subagent Complete"

### CLAUDE_HOOKS_SUMMARY_VERBOSITY
**Default:** `brief`  
**Values:** `brief` | `detailed`

Control the verbosity level of generated summaries.

```bash
# Brief summaries (default) - optimized for TTS
export CLAUDE_HOOKS_SUMMARY_VERBOSITY=brief

# Detailed summaries - more comprehensive information
export CLAUDE_HOOKS_SUMMARY_VERBOSITY=detailed
```

### ENGINEER_NAME
**Default:** None  
**Values:** Any string

Personalize notifications by including your name occasionally.

```bash
# Add personalization to notifications
export ENGINEER_NAME="Alex"
```

When set, there's a 30% chance that notification messages will include your name:
- "Alex, working on authentication, needs your input"
- "Your agent needs your input" (70% of the time)

## Configuration Examples

### Minimal Setup
```bash
# Just enable intelligent summaries with defaults
export CLAUDE_HOOKS_SUMMARY_ENABLED=true
```

### Full Configuration
```bash
# Complete setup with personalization
export CLAUDE_HOOKS_SUMMARY_ENABLED=true
export CLAUDE_HOOKS_SUMMARY_VERBOSITY=brief
export ENGINEER_NAME="YourName"
export OPENAI_API_KEY="your-openai-key"  # For TTS
```

### Disable Intelligent Summaries
```bash
# Fall back to original generic messages
export CLAUDE_HOOKS_SUMMARY_ENABLED=false
```

## Setting Environment Variables

### Option 1: Shell Profile
Add to your `~/.bashrc`, `~/.zshrc`, or similar:

```bash
# Claude Code Hooks Configuration
export CLAUDE_HOOKS_SUMMARY_ENABLED=true
export CLAUDE_HOOKS_SUMMARY_VERBOSITY=brief
export ENGINEER_NAME="YourName"
```

### Option 2: Project .env File
Create a `.env` file in your project directory:

```bash
# .env file
CLAUDE_HOOKS_SUMMARY_ENABLED=true
CLAUDE_HOOKS_SUMMARY_VERBOSITY=brief
ENGINEER_NAME=YourName
OPENAI_API_KEY=your-openai-key
```

### Option 3: Global .env File
Create a `.env` file in your home directory:

```bash
# ~/.env file
CLAUDE_HOOKS_SUMMARY_ENABLED=true
CLAUDE_HOOKS_SUMMARY_VERBOSITY=brief
ENGINEER_NAME=YourName
```

## Hook-Specific Behavior

### Stop Hook (`stop.py`)
Generates completion summaries like:
- **Brief:** "Completed: created auth.py, modified 2 files, ran tests"
- **Detailed:** "Completed: created authentication system in auth.py, modified user.py and routes.py, successfully ran test suite with 15 passing tests"

### Notification Hook (`notification.py`)
Generates context-aware input requests like:
- **Brief:** "Working on database setup, needs your input"
- **Detailed:** "Setting up PostgreSQL database configuration, needs your choice between development and production schemas"

### SubagentStop Hook (`subagent_stop.py`)
Generates subagent accomplishment summaries like:
- **Brief:** "Subagent analyzed 5 React components"
- **Detailed:** "Subagent completed security analysis of 5 React components, identified 2 potential vulnerabilities"

## Fallback Behavior

The system is designed to be robust with multiple fallback layers:

1. **Primary:** Intelligent summary generation
2. **Secondary:** Generic messages if analysis fails
3. **Tertiary:** Silent failure if TTS is unavailable

This ensures your hooks always work, even if:
- Transcript files are missing or corrupted
- Analysis libraries have issues
- TTS services are unavailable
- Network connectivity is poor

## Troubleshooting

### Summaries Not Working
1. Check that `CLAUDE_HOOKS_SUMMARY_ENABLED=true`
2. Verify transcript files exist in `~/.claude/projects/`
3. Test with a simple session to ensure analysis works

### Generic Messages Still Appearing
This is expected behavior when:
- No meaningful activity occurred in the session
- Transcript analysis fails
- `CLAUDE_HOOKS_SUMMARY_ENABLED=false`

### TTS Not Working
Intelligent summaries are generated independently of TTS. If you see summaries in logs but no audio:
- Check `OPENAI_API_KEY` is set
- Verify TTS scripts exist in `~/.claude/hooks/utils/tts/`
- Test TTS directly: `uv run ~/.claude/hooks/utils/tts/openai_tts_fixed.py "test message"`

## Example Session Summaries

### Coding Session
```
Stop: "Completed: created user-auth.py, modified routes.py, ran tests successfully"
```

### Research Session
```
Stop: "Completed: analyzed 12 files, researched React patterns"
Subagent: "Subagent analyzed authentication patterns in 8 components"
```

### Debugging Session
```
Stop: "Completed: fixed 3 TypeScript errors, updated dependencies"
Notification: "Debugging test failures, needs your input on mock data"
```

### Configuration Session
```
Stop: "Completed: updated database config, modified 4 environment files"
Notification: "Configuring deployment settings, needs your choice of staging server"
```