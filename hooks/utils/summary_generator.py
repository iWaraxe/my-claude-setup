#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
# ]
# ///

import os
import random
from typing import List, Optional
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import our transcript analyzer
try:
    from transcript_analyzer import SessionAnalysis, FileOperation, BashCommand
except ImportError:
    # Fallback for when called from hooks
    import sys
    sys.path.append(str(Path(__file__).parent))
    from transcript_analyzer import SessionAnalysis, FileOperation, BashCommand

class SummaryGenerator:
    """Generates concise, TTS-friendly summaries of Claude Code sessions."""
    
    def __init__(self):
        self.max_tts_length = 80  # Optimal length for TTS
        self.fallback_stop_messages = [
            "Work complete!",
            "All done!",
            "Task finished!",
            "Job complete!",
            "Ready for next task!"
        ]
        self.fallback_notification_messages = [
            "Your agent needs your input",
            "Waiting for your response",
            "Input required to continue"
        ]
        self.fallback_subagent_messages = [
            "Subagent Complete",
            "Subagent task finished",
            "Background work done"
        ]
        
    def generate_stop_summary(self, analysis: SessionAnalysis) -> str:
        """
        Generate a completion summary for the Stop hook.
        
        Args:
            analysis: Analyzed session data
            
        Returns:
            Concise summary of what was accomplished
        """
        # Check if summary generation is disabled
        if not self._is_summary_enabled():
            return random.choice(self.fallback_stop_messages)
        
        try:
            # If no meaningful activity, use fallback
            if not analysis.key_accomplishments and not analysis.file_operations and not analysis.bash_commands:
                return random.choice(self.fallback_stop_messages)
            
            summary_parts = []
            
            # File operations summary
            file_summary = self._summarize_file_operations(analysis.file_operations)
            if file_summary:
                summary_parts.append(file_summary)
            
            # Command execution summary
            command_summary = self._summarize_bash_commands(analysis.bash_commands)
            if command_summary:
                summary_parts.append(command_summary)
            
            # Error summary
            error_summary = self._summarize_errors(analysis.errors)
            if error_summary:
                summary_parts.append(error_summary)
            
            # Combine and truncate for TTS
            if summary_parts:
                full_summary = "Completed: " + ", ".join(summary_parts)
                return self._truncate_for_tts(full_summary)
            else:
                # Use accomplishments if available
                if analysis.key_accomplishments:
                    accomplishment_text = ", ".join(analysis.key_accomplishments[:2])
                    return self._truncate_for_tts(f"Completed: {accomplishment_text}")
                else:
                    return random.choice(self.fallback_stop_messages)
                    
        except Exception:
            # Fallback on any error
            return random.choice(self.fallback_stop_messages)
    
    def generate_notification_summary(self, analysis: SessionAnalysis) -> str:
        """
        Generate a context-aware notification for when Claude needs input.
        
        Args:
            analysis: Analyzed session data
            
        Returns:
            Context-aware message about what's happening and what input is needed
        """
        # Check if summary generation is disabled
        if not self._is_summary_enabled():
            return random.choice(self.fallback_notification_messages)
        
        try:
            # Get engineer name for personalization
            engineer_name = os.getenv('ENGINEER_NAME', '').strip()
            name_prefix = f"{engineer_name}, " if engineer_name and random.random() < 0.3 else ""
            
            # Use current context if available
            if analysis.current_context and analysis.current_context != "Unknown context":
                context_msg = f"Working on: {analysis.current_context}, needs your input"
                return self._truncate_for_tts(name_prefix + context_msg)
            
            # Generate context from recent activity
            recent_context = self._generate_notification_context(analysis)
            if recent_context:
                context_msg = f"{recent_context}, needs your input"
                return self._truncate_for_tts(name_prefix + context_msg)
            
            # Fallback to generic message
            return name_prefix + random.choice(self.fallback_notification_messages)
            
        except Exception:
            return random.choice(self.fallback_notification_messages)
    
    def generate_subagent_summary(self, analysis: SessionAnalysis) -> str:
        """
        Generate a summary for subagent completion.
        
        Args:
            analysis: Analyzed session data
            
        Returns:
            Summary of what the subagent accomplished
        """
        # Check if summary generation is disabled
        if not self._is_summary_enabled():
            return random.choice(self.fallback_subagent_messages)
        
        try:
            # Subagents are typically research/analysis tasks
            research_summary = self._summarize_research_activity(analysis)
            if research_summary:
                return self._truncate_for_tts(f"Subagent completed: {research_summary}")
            
            # File analysis summary
            if analysis.file_operations:
                file_count = len([op for op in analysis.file_operations if op.operation == 'read'])
                if file_count > 0:
                    return self._truncate_for_tts(f"Subagent analyzed {file_count} files")
            
            # Generic summary with accomplishments
            if analysis.key_accomplishments:
                accomplishment = analysis.key_accomplishments[0]
                return self._truncate_for_tts(f"Subagent completed: {accomplishment}")
            
            return random.choice(self.fallback_subagent_messages)
            
        except Exception:
            return random.choice(self.fallback_subagent_messages)
    
    def _summarize_file_operations(self, file_operations: List[FileOperation]) -> str:
        """Summarize file operations into a concise string."""
        if not file_operations:
            return ""
        
        created = [op for op in file_operations if op.operation == 'write' and op.success]
        modified = [op for op in file_operations if op.operation == 'edit' and op.success]
        
        parts = []
        if created:
            if len(created) == 1:
                filename = Path(created[0].file_path).name
                parts.append(f"created {filename}")
            else:
                parts.append(f"created {len(created)} files")
        
        if modified:
            if len(modified) == 1 and not created:
                filename = Path(modified[0].file_path).name
                parts.append(f"modified {filename}")
            else:
                parts.append(f"modified {len(modified)} files")
        
        return ", ".join(parts)
    
    def _summarize_bash_commands(self, bash_commands: List[BashCommand]) -> str:
        """Summarize bash command executions."""
        if not bash_commands:
            return ""
        
        successful = [cmd for cmd in bash_commands if cmd.success]
        if not successful:
            return ""
        
        # Categorize commands
        test_commands = [cmd for cmd in successful if 'test' in cmd.command.lower()]
        build_commands = [cmd for cmd in successful if any(keyword in cmd.command.lower() 
                         for keyword in ['build', 'compile', 'npm run', 'yarn', 'make'])]
        git_commands = [cmd for cmd in successful if cmd.command.startswith('git')]
        
        parts = []
        if test_commands:
            parts.append("ran tests")
        if build_commands:
            parts.append("built project")
        if git_commands:
            parts.append("updated git")
        
        # If no specific categories, just count commands
        if not parts and len(successful) > 0:
            parts.append(f"executed {len(successful)} commands")
        
        return ", ".join(parts)
    
    def _summarize_errors(self, errors: List[str]) -> str:
        """Summarize any errors that occurred."""
        if not errors:
            return ""
        
        error_count = len(errors)
        if error_count == 1:
            return "resolved 1 error"
        elif error_count > 1:
            return f"resolved {error_count} errors"
        
        return ""
    
    def _generate_notification_context(self, analysis: SessionAnalysis) -> str:
        """Generate context for notification messages."""
        # Look at recent file operations
        if analysis.file_operations:
            recent_files = analysis.file_operations[-2:]
            if len(recent_files) == 1:
                filename = Path(recent_files[0].file_path).name
                return f"Working on {filename}"
            elif len(recent_files) > 1:
                return "Working on multiple files"
        
        # Look at recent user messages for context
        if analysis.user_messages:
            last_message = analysis.user_messages[-1]
            # Extract key topics from the message
            if any(keyword in last_message.lower() for keyword in ['database', 'db']):
                return "Setting up database"
            elif any(keyword in last_message.lower() for keyword in ['test', 'testing']):
                return "Working on tests"
            elif any(keyword in last_message.lower() for keyword in ['auth', 'authentication']):
                return "Implementing authentication"
            elif any(keyword in last_message.lower() for keyword in ['api', 'endpoint']):
                return "Building API"
        
        return ""
    
    def _summarize_research_activity(self, analysis: SessionAnalysis) -> str:
        """Summarize research/analysis activities for subagents."""
        research_tools = {'WebFetch', 'WebSearch', 'Grep', 'Glob', 'LS'}
        research_events = [event for event in analysis.tool_events 
                          if event.tool_name in research_tools]
        
        if research_events:
            if len(research_events) == 1:
                return "conducted code analysis"
            else:
                return f"analyzed {len(research_events)} code components"
        
        return ""
    
    def _is_summary_enabled(self) -> bool:
        """Check if intelligent summaries are enabled."""
        return os.getenv('CLAUDE_HOOKS_SUMMARY_ENABLED', 'true').lower() == 'true'
    
    def _get_verbosity_level(self) -> str:
        """Get the configured verbosity level."""
        return os.getenv('CLAUDE_HOOKS_SUMMARY_VERBOSITY', 'brief').lower()
    
    def _truncate_for_tts(self, text: str) -> str:
        """Truncate text to optimal length for TTS."""
        if len(text) <= self.max_tts_length:
            return text
        
        # Try to truncate at a word boundary
        truncated = text[:self.max_tts_length]
        last_space = truncated.rfind(' ')
        if last_space > self.max_tts_length * 0.7:  # If we can find a reasonable word boundary
            return truncated[:last_space]
        else:
            return truncated.rstrip() + "..."

# Example usage and testing
if __name__ == "__main__":
    import sys
    from transcript_analyzer import TranscriptAnalyzer
    
    if len(sys.argv) > 1:
        transcript_path = sys.argv[1]
        hook_type = sys.argv[2] if len(sys.argv) > 2 else "stop"
        
        # Analyze transcript
        analyzer = TranscriptAnalyzer()
        analysis = analyzer.analyze_transcript(transcript_path)
        
        # Generate summary
        generator = SummaryGenerator()
        
        if hook_type == "stop":
            summary = generator.generate_stop_summary(analysis)
        elif hook_type == "notification":
            summary = generator.generate_notification_summary(analysis)
        elif hook_type == "subagent":
            summary = generator.generate_subagent_summary(analysis)
        else:
            summary = generator.generate_stop_summary(analysis)
        
        print(summary)
    else:
        print("Usage: python summary_generator.py <transcript_path> [stop|notification|subagent]")