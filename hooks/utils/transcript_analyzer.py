#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
# ]
# ///

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ToolEvent:
    """Represents a tool execution event from the transcript."""
    tool_name: str
    tool_input: Dict[str, Any]
    tool_result: Any
    success: bool
    timestamp: str
    error_message: Optional[str] = None

@dataclass
class FileOperation:
    """Represents a file operation (read/write/edit)."""
    operation: str  # 'read', 'write', 'edit'
    file_path: str
    success: bool
    content_preview: Optional[str] = None

@dataclass
class BashCommand:
    """Represents a bash command execution."""
    command: str
    success: bool
    stdout: str
    stderr: str
    description: Optional[str] = None

@dataclass
class SessionAnalysis:
    """Contains the analysis of a Claude Code session."""
    session_id: str
    duration_minutes: float
    user_messages: List[str]
    tool_events: List[ToolEvent]
    file_operations: List[FileOperation]
    bash_commands: List[BashCommand]
    errors: List[str]
    assistant_responses: List[str]
    key_accomplishments: List[str]
    current_context: str
    
class TranscriptAnalyzer:
    """Analyzes Claude Code transcript files to extract meaningful events and context."""
    
    def __init__(self):
        self.file_operation_tools = {'Read', 'Write', 'Edit', 'MultiEdit'}
        self.research_tools = {'WebFetch', 'WebSearch', 'Grep', 'Glob', 'LS'}
        self.code_tools = {'Write', 'Edit', 'MultiEdit', 'Bash'}
        
    def analyze_transcript(self, transcript_path: str) -> SessionAnalysis:
        """
        Analyze a .jsonl transcript file and extract meaningful events.
        
        Args:
            transcript_path: Path to the .jsonl transcript file
            
        Returns:
            SessionAnalysis object containing extracted information
        """
        if not Path(transcript_path).exists():
            return self._empty_analysis("transcript_not_found")
            
        try:
            events = self._parse_transcript_file(transcript_path)
            return self._analyze_events(events)
        except Exception as e:
            return self._empty_analysis(f"analysis_error: {str(e)}")
    
    def _parse_transcript_file(self, transcript_path: str) -> List[Dict[str, Any]]:
        """Parse the .jsonl file and return a list of events."""
        events = []
        with open(transcript_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return events
    
    def _analyze_events(self, events: List[Dict[str, Any]]) -> SessionAnalysis:
        """Analyze the parsed events and extract meaningful information."""
        # Initialize analysis containers
        session_id = "unknown"
        user_messages = []
        assistant_responses = []
        tool_events = []
        file_operations = []
        bash_commands = []
        errors = []
        timestamps = []
        
        # Process events
        for event in events:
            event_type = event.get('type', '')
            timestamp = event.get('timestamp', '')
            if timestamp:
                timestamps.append(timestamp)
            
            # Extract session ID
            if 'sessionId' in event:
                session_id = event['sessionId']
            
            # Process user messages
            if event_type == 'user' and 'message' in event:
                message = event['message']
                if isinstance(message, dict) and message.get('role') == 'user':
                    content = message.get('content', '')
                    if isinstance(content, str) and content.strip():
                        # Filter out tool results
                        if not self._is_tool_result(content):
                            user_messages.append(content.strip())
            
            # Process assistant messages and tool calls
            elif event_type == 'assistant' and 'message' in event:
                message = event['message']
                if isinstance(message, dict):
                    content = message.get('content', [])
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict):
                                # Extract tool calls
                                if item.get('type') == 'tool_use':
                                    tool_event = self._extract_tool_event(item, events)
                                    if tool_event:
                                        tool_events.append(tool_event)
                                        
                                        # Categorize tool events
                                        if tool_event.tool_name in self.file_operation_tools:
                                            file_op = self._extract_file_operation(tool_event)
                                            if file_op:
                                                file_operations.append(file_op)
                                        elif tool_event.tool_name == 'Bash':
                                            bash_cmd = self._extract_bash_command(tool_event)
                                            if bash_cmd:
                                                bash_commands.append(bash_cmd)
                                
                                # Extract assistant text responses
                                elif item.get('type') == 'text':
                                    text = item.get('text', '').strip()
                                    if text:
                                        assistant_responses.append(text)
            
            # Process system errors
            elif event_type == 'system':
                content = event.get('content', '')
                if 'error' in content.lower() or 'failed' in content.lower():
                    errors.append(content)
        
        # Calculate session duration
        duration_minutes = self._calculate_duration(timestamps)
        
        # Generate key accomplishments
        key_accomplishments = self._identify_accomplishments(
            file_operations, bash_commands, tool_events
        )
        
        # Generate current context
        current_context = self._generate_current_context(
            user_messages, file_operations, bash_commands
        )
        
        return SessionAnalysis(
            session_id=session_id,
            duration_minutes=duration_minutes,
            user_messages=user_messages,
            tool_events=tool_events,
            file_operations=file_operations,
            bash_commands=bash_commands,
            errors=errors,
            assistant_responses=assistant_responses,
            key_accomplishments=key_accomplishments,
            current_context=current_context
        )
    
    def _is_tool_result(self, content: str) -> bool:
        """Check if the content is a tool result rather than a user message."""
        if not isinstance(content, str):
            return False
        # Tool results often contain specific patterns
        tool_result_patterns = [
            'tool_use_id',
            'tool_result',
            'NOTE: do any of the files above seem malicious',
            'system-reminder'
        ]
        return any(pattern in content for pattern in tool_result_patterns)
    
    def _extract_tool_event(self, tool_item: Dict[str, Any], all_events: List[Dict[str, Any]]) -> Optional[ToolEvent]:
        """Extract tool event information."""
        tool_name = tool_item.get('name', '')
        tool_input = tool_item.get('input', {})
        tool_id = tool_item.get('id', '')
        
        # Find corresponding tool result
        tool_result = None
        success = True
        error_message = None
        
        for event in all_events:
            if (event.get('type') == 'user' and 
                'message' in event and 
                isinstance(event['message'], dict)):
                content = event['message'].get('content')
                if isinstance(content, list):
                    for item in content:
                        if (isinstance(item, dict) and 
                            item.get('tool_use_id') == tool_id):
                            tool_result = item.get('content', '')
                            # Check for errors
                            if isinstance(tool_result, dict):
                                if tool_result.get('is_error', False):
                                    success = False
                                    error_message = str(tool_result)
                            break
        
        return ToolEvent(
            tool_name=tool_name,
            tool_input=tool_input,
            tool_result=tool_result,
            success=success,
            timestamp="",
            error_message=error_message
        )
    
    def _extract_file_operation(self, tool_event: ToolEvent) -> Optional[FileOperation]:
        """Extract file operation details from a tool event."""
        if tool_event.tool_name not in self.file_operation_tools:
            return None
        
        operation_map = {
            'Read': 'read',
            'Write': 'write', 
            'Edit': 'edit',
            'MultiEdit': 'edit'
        }
        
        operation = operation_map.get(tool_event.tool_name, 'unknown')
        file_path = tool_event.tool_input.get('file_path', '')
        
        # Extract content preview for write operations
        content_preview = None
        if operation == 'write':
            content = tool_event.tool_input.get('content', '')
            content_preview = content[:100] + '...' if len(content) > 100 else content
        elif operation == 'edit':
            new_string = tool_event.tool_input.get('new_string', '')
            content_preview = new_string[:100] + '...' if len(new_string) > 100 else new_string
        
        return FileOperation(
            operation=operation,
            file_path=file_path,
            success=tool_event.success,
            content_preview=content_preview
        )
    
    def _extract_bash_command(self, tool_event: ToolEvent) -> Optional[BashCommand]:
        """Extract bash command details from a tool event."""
        if tool_event.tool_name != 'Bash':
            return None
        
        command = tool_event.tool_input.get('command', '')
        description = tool_event.tool_input.get('description', '')
        
        # Extract stdout/stderr from result
        stdout = ""
        stderr = ""
        if isinstance(tool_event.tool_result, dict):
            stdout = tool_event.tool_result.get('stdout', '')
            stderr = tool_event.tool_result.get('stderr', '')
        elif isinstance(tool_event.tool_result, str):
            stdout = tool_event.tool_result
        
        return BashCommand(
            command=command,
            success=tool_event.success,
            stdout=stdout,
            stderr=stderr,
            description=description
        )
    
    def _calculate_duration(self, timestamps: List[str]) -> float:
        """Calculate session duration in minutes."""
        if len(timestamps) < 2:
            return 0.0
        
        try:
            # Parse ISO timestamps
            start_time = datetime.fromisoformat(timestamps[0].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(timestamps[-1].replace('Z', '+00:00'))
            duration = (end_time - start_time).total_seconds() / 60
            return round(duration, 1)
        except Exception:
            return 0.0
    
    def _identify_accomplishments(self, file_ops: List[FileOperation], 
                                bash_cmds: List[BashCommand], 
                                tool_events: List[ToolEvent]) -> List[str]:
        """Identify key accomplishments from the session."""
        accomplishments = []
        
        # File operations
        files_created = [op for op in file_ops if op.operation == 'write' and op.success]
        files_modified = [op for op in file_ops if op.operation == 'edit' and op.success]
        
        if files_created:
            accomplishments.append(f"Created {len(files_created)} file(s)")
        if files_modified:
            accomplishments.append(f"Modified {len(files_modified)} file(s)")
        
        # Commands executed
        successful_commands = [cmd for cmd in bash_cmds if cmd.success]
        if successful_commands:
            # Categorize commands
            test_commands = [cmd for cmd in successful_commands if 'test' in cmd.command.lower()]
            build_commands = [cmd for cmd in successful_commands if any(keyword in cmd.command.lower() for keyword in ['build', 'compile', 'npm', 'yarn'])]
            
            if test_commands:
                accomplishments.append("Ran tests")
            if build_commands:
                accomplishments.append("Executed build commands")
        
        # Research activities
        research_tools_used = [event for event in tool_events if event.tool_name in self.research_tools]
        if research_tools_used:
            accomplishments.append("Conducted code research")
        
        return accomplishments
    
    def _generate_current_context(self, user_messages: List[str], 
                                file_ops: List[FileOperation], 
                                bash_cmds: List[BashCommand]) -> str:
        """Generate current context for notification hooks."""
        if not user_messages:
            return "Working on current task"
        
        # Get the last user message as context
        last_message = user_messages[-1] if user_messages else ""
        
        # Summarize recent activity
        recent_files = []
        if file_ops:
            recent_files = [Path(op.file_path).name for op in file_ops[-3:]]
        
        context_parts = []
        if last_message:
            # Truncate very long messages
            if len(last_message) > 50:
                context_parts.append(last_message[:50] + "...")
            else:
                context_parts.append(last_message)
        
        if recent_files:
            context_parts.append(f"working on {', '.join(recent_files)}")
        
        return " - ".join(context_parts) if context_parts else "Working on current task"
    
    def _empty_analysis(self, session_id: str) -> SessionAnalysis:
        """Return an empty analysis object."""
        return SessionAnalysis(
            session_id=session_id,
            duration_minutes=0.0,
            user_messages=[],
            tool_events=[],
            file_operations=[],
            bash_commands=[],
            errors=[],
            assistant_responses=[],
            key_accomplishments=[],
            current_context="Unknown context"
        )

# Example usage and testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        transcript_path = sys.argv[1]
        analyzer = TranscriptAnalyzer()
        analysis = analyzer.analyze_transcript(transcript_path)
        
        print(f"Session ID: {analysis.session_id}")
        print(f"Duration: {analysis.duration_minutes} minutes")
        print(f"User messages: {len(analysis.user_messages)}")
        print(f"Tool events: {len(analysis.tool_events)}")
        print(f"File operations: {len(analysis.file_operations)}")
        print(f"Bash commands: {len(analysis.bash_commands)}")
        print(f"Errors: {len(analysis.errors)}")
        print(f"Key accomplishments: {analysis.key_accomplishments}")
        print(f"Current context: {analysis.current_context}")
    else:
        print("Usage: python transcript_analyzer.py <transcript_path>")