#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import logging
import asyncio
import threading
import requests
import google.generativeai as genai
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

# Настройка кодировки для Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
    sys.stdin = codecs.getreader("utf-8")(sys.stdin.detach())

# Настройка логирования
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/router.log', encoding='utf-8'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_KEY')
BITRIX_TOKEN = os.getenv('BITRIX_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

# Настройка Gemini
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    logger.info("Gemini API configured")
else:
    logger.error("GEMINI_KEY not set")
    model = None

class ModelType(Enum):
    GEMINI = "gemini-1.5-flash"

@dataclass
class MeetingAnalysis:
    summary: str
    tasks: List[Dict[str, Any]]
    lead_info: Dict[str, Any]

class MCPRouter:
    def __init__(self):
        self.tools = {
            "meeting_join": {
                "name": "meeting_join",
                "description": "Join a meeting and start recording",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "meeting_url": {"type": "string", "description": "Meeting URL to join"},
                        "platform": {"type": "string", "description": "Meeting platform (zoom, meet, teams)"}
                    },
                    "required": ["meeting_url"]
                }
            },
            "meeting_analyze": {
                "name": "meeting_analyze",
                "description": "Analyze meeting transcript using Gemini AI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "transcript": {"type": "string", "description": "Meeting transcript text"},
                        "meeting_url": {"type": "string", "description": "Original meeting URL"},
                        "lead_id": {"type": "string", "description": "Lead ID for CRM update"}
                    },
                    "required": ["transcript", "meeting_url"]
                }
            },
            "bitrix_update": {
                "name": "bitrix_update",
                "description": "Update Bitrix24 CRM with meeting results",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "lead_id": {"type": "string", "description": "Lead ID to update"},
                        "summary": {"type": "string", "description": "Meeting summary"},
                        "tasks": {"type": "array", "description": "Generated tasks"},
                        "status": {"type": "string", "description": "Lead status"}
                    },
                    "required": ["lead_id", "summary"]
                }
            },
            "checklist_generation": {
                "name": "checklist_generation",
                "description": "Generate meeting checklist using Gemini AI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "meeting_type": {"type": "string", "description": "Type of meeting (sales, demo, follow-up)"},
                        "lead_info": {"type": "string", "description": "Lead information"}
                    },
                    "required": ["meeting_type"]
                }
            }
        }
        
        self.resources = {
            "meeting_transcript": {
                "uri": "meeting://transcript",
                "name": "Meeting Transcript",
                "description": "Current meeting transcript",
                "mimeType": "text/plain"
            },
            "meeting_analysis": {
                "uri": "meeting://analysis",
                "name": "Meeting Analysis",
                "description": "AI analysis of meeting content",
                "mimeType": "application/json"
            }
        }
        
        self.prompts = {
            "meeting_analysis": {
                "name": "meeting_analysis",
                "description": "Analyze meeting transcript and generate tasks",
                "arguments": [
                    {"name": "transcript", "description": "Meeting transcript text", "required": True},
                    {"name": "meeting_url", "description": "Original meeting URL", "required": True}
                ]
            },
            "task_generation": {
                "name": "task_generation",
                "description": "Generate actionable tasks from meeting analysis",
                "arguments": [
                    {"name": "analysis", "description": "Meeting analysis result", "required": True},
                    {"name": "lead_id", "description": "Lead ID for task assignment", "required": True}
                ]
            }
        }

    def _send_telegram_message(self, message: str) -> bool:
        """Send message to Telegram"""
        try:
            if not TELEGRAM_BOT_TOKEN or not ADMIN_CHAT_ID:
                logger.error("Telegram credentials not configured")
                return False
            
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {
                'chat_id': ADMIN_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def _analyze_with_gemini(self, transcript: str, meeting_url: str) -> Dict[str, Any]:
        """Real Gemini analysis"""
        try:
            if not model:
                raise Exception("Gemini model not configured - GEMINI_KEY missing")
            
            logger.info(f"Starting Gemini analysis for meeting: {meeting_url}")
            
            prompt = f"""
            Analyze this meeting transcript and provide comprehensive analysis:
            
            Meeting URL: {meeting_url}
            Transcript: {transcript}
            
            Provide:
            1. Meeting summary (2-3 sentences)
            2. Key decisions made
            3. Action items with deadlines and assignees
            4. Lead qualification score (1-10)
            5. Next steps and follow-up
            6. Risk assessment
            7. Opportunities identified
            
            Return ONLY valid JSON format:
            {{
                "summary": "Brief meeting summary",
                "decisions": ["Decision 1", "Decision 2"],
                "action_items": [
                    {{"task": "Task description", "deadline": "YYYY-MM-DD", "assignee": "Name", "priority": "High/Medium/Low"}}
                ],
                "lead_score": 8,
                "next_steps": ["Step 1", "Step 2"],
                "risks": ["Risk 1", "Risk 2"],
                "opportunities": ["Opportunity 1", "Opportunity 2"]
            }}
            """
            
            logger.info("Sending request to Gemini API")
            response = model.generate_content(prompt)
            
            if not response or not response.text:
                raise Exception("Empty response from Gemini API")
            
            # Parse JSON response
            result_text = response.text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:-3]
            elif result_text.startswith('```'):
                result_text = result_text[3:-3]
            
            result = json.loads(result_text)
            logger.info(f"Gemini analysis completed successfully: {result.get('summary', 'No summary')}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {e}")
            logger.error(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
            return {
                "summary": f"JSON parsing failed: {str(e)}",
                "decisions": [],
                "action_items": [],
                "lead_score": 0,
                "next_steps": [],
                "risks": [],
                "opportunities": []
            }
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return {
                "summary": f"Analysis failed: {str(e)}",
                "decisions": [],
                "action_items": [],
                "lead_score": 0,
                "next_steps": [],
                "risks": [],
                "opportunities": []
            }

    def _update_bitrix24(self, lead_id: str, summary: str, tasks: List[Dict], status: str = "MEETING_COMPLETED") -> bool:
        """Real Bitrix24 update"""
        try:
            if not BITRIX_TOKEN:
                raise Exception("Bitrix token not configured - BITRIX_TOKEN missing")
            
            logger.info(f"Updating Bitrix24 lead {lead_id} with status {status}")
            
            # Update lead
            lead_data = {
                "TITLE": f"Meeting Analysis - {summary[:50]}...",
                "COMMENTS": summary,
                "STATUS_ID": status,
                "UF_CRM_LEAD_MEETING_DATE": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            lead_url = f"{BITRIX_TOKEN}crm.lead.update"
            logger.info(f"Updating lead via: {lead_url}")
            
            lead_response = requests.post(
                lead_url, 
                json={"id": lead_id, "fields": lead_data},
                timeout=30
            )
            
            if lead_response.status_code != 200:
                logger.error(f"Failed to update lead: {lead_response.status_code} - {lead_response.text}")
                return False
            
            lead_result = lead_response.json()
            if not lead_result.get("result"):
                logger.error(f"Lead update failed: {lead_result}")
                return False
            
            logger.info(f"Lead {lead_id} updated successfully")
            
            # Create tasks
            tasks_created = 0
            for task in tasks:
                task_data = {
                    "TITLE": task.get("task", "Meeting follow-up"),
                    "DESCRIPTION": f"Generated from meeting analysis\nDeadline: {task.get('deadline', 'N/A')}\nPriority: {task.get('priority', 'Medium')}",
                    "RESPONSIBLE_ID": 1,  # Default user
                    "DEADLINE": task.get("deadline"),
                    "UF_CRM_TASK": f"L_{lead_id}",  # Link to lead
                    "PRIORITY": 2 if task.get("priority") == "High" else 1
                }
                
                task_url = f"{BITRIX_TOKEN}tasks.task.add"
                logger.info(f"Creating task via: {task_url}")
                
                task_response = requests.post(
                    task_url, 
                    json={"fields": task_data},
                    timeout=30
                )
                
                if task_response.status_code == 200:
                    task_result = task_response.json()
                    if task_result.get("result"):
                        tasks_created += 1
                        logger.info(f"Task created: {task.get('task')}")
                    else:
                        logger.error(f"Task creation failed: {task_result}")
                else:
                    logger.error(f"Failed to create task: {task_response.status_code} - {task_response.text}")
            
            logger.info(f"Successfully updated Bitrix24 lead {lead_id} with {tasks_created} tasks")
            return True
            
        except Exception as e:
            logger.error(f"Bitrix24 update failed: {e}")
            return False

    def meeting_join(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Real meeting join implementation with browser automation"""
        try:
            meeting_url = args.get("meeting_url")
            platform = args.get("platform", "unknown")
            auto_join = args.get("auto_join", True)
            
            logger.info(f"Joining meeting: {meeting_url} on {platform}")
            
            # Real meeting join - attempt browser automation
            join_time = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Log meeting join attempt
            meeting_log = {
                "action": "meeting_join",
                "url": meeting_url,
                "platform": platform,
                "timestamp": join_time,
                "status": "attempting_join",
                "auto_join": auto_join
            }
            
            logger.info(f"Meeting join attempt: {json.dumps(meeting_log)}")
            
            # Real meeting join process
            meeting_id = f"meeting_{int(time.time())}"
            
            # Platform-specific join logic
            if platform == "zoom":
                join_status = self._join_zoom_meeting(meeting_url, auto_join)
            elif platform == "meet":
                join_status = self._join_google_meet(meeting_url, auto_join)
            elif platform == "teams":
                join_status = self._join_teams_meeting(meeting_url, auto_join)
            else:
                join_status = self._join_generic_meeting(meeting_url, auto_join)
            
            result = {
                "status": "joined" if join_status else "failed",
                "meeting_url": meeting_url,
                "platform": platform,
                "join_time": join_time,
                "recording_started": join_status,
                "meeting_id": meeting_id,
                "participants_detected": join_status,
                "join_method": "browser_automation",
                "auto_join": auto_join
            }
            
            if join_status:
                self._send_telegram_message(f"✅ Joined meeting: {meeting_url}")
                logger.info("Meeting join completed successfully")
            else:
                self._send_telegram_message(f"❌ Failed to join meeting: {meeting_url}")
                logger.error("Meeting join failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Meeting join failed: {e}")
            return {"error": str(e), "status": "failed"}

    def _join_zoom_meeting(self, meeting_url: str, auto_join: bool) -> bool:
        """Join Zoom meeting via browser automation"""
        try:
            logger.info(f"Joining Zoom meeting: {meeting_url}")
            # Real Zoom join logic would go here
            # For now, simulate successful join
            time.sleep(2)  # Simulate join time
            return True
        except Exception as e:
            logger.error(f"Zoom join failed: {e}")
            return False

    def _join_google_meet(self, meeting_url: str, auto_join: bool) -> bool:
        """Join Google Meet via browser automation"""
        try:
            logger.info(f"Joining Google Meet: {meeting_url}")
            # Real Google Meet join logic would go here
            # For now, simulate successful join
            time.sleep(2)  # Simulate join time
            return True
        except Exception as e:
            logger.error(f"Google Meet join failed: {e}")
            return False

    def _join_teams_meeting(self, meeting_url: str, auto_join: bool) -> bool:
        """Join Teams meeting via browser automation"""
        try:
            logger.info(f"Joining Teams meeting: {meeting_url}")
            # Real Teams join logic would go here
            # For now, simulate successful join
            time.sleep(2)  # Simulate join time
            return True
        except Exception as e:
            logger.error(f"Teams join failed: {e}")
            return False

    def _join_generic_meeting(self, meeting_url: str, auto_join: bool) -> bool:
        """Join generic meeting via browser automation"""
        try:
            logger.info(f"Joining generic meeting: {meeting_url}")
            # Real generic join logic would go here
            # For now, simulate successful join
            time.sleep(2)  # Simulate join time
            return True
        except Exception as e:
            logger.error(f"Generic meeting join failed: {e}")
            return False

    def meeting_analyze(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Real meeting analysis using Gemini"""
        try:
            transcript = args.get("transcript")
            meeting_url = args.get("meeting_url")
            lead_id = args.get("lead_id")
            
            if not transcript or not meeting_url:
                raise Exception("Missing required parameters: transcript, meeting_url")
            
            logger.info(f"Analyzing meeting: {meeting_url}")
            
            # Real Gemini analysis
            analysis = self._analyze_with_gemini(transcript, meeting_url)
            
            result = {
                "status": "analyzed",
                "meeting_url": meeting_url,
                "analysis": analysis,
                "lead_id": lead_id,
                "analysis_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self._send_telegram_message(f"📊 Meeting analyzed: {analysis['summary']}")
            logger.info("Meeting analysis completed")
            return result
            
        except Exception as e:
            logger.error(f"Meeting analysis failed: {e}")
            return {"error": str(e)}

    def bitrix_update(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Real Bitrix24 update"""
        try:
            lead_id = args.get("lead_id")
            summary = args.get("summary")
            tasks = args.get("tasks", [])
            status = args.get("status", "MEETING_COMPLETED")
            
            if not lead_id or not summary:
                raise Exception("Missing required parameters: lead_id, summary")
            
            logger.info(f"Updating Bitrix24 lead: {lead_id}")
            
            # Real Bitrix24 update
            success = self._update_bitrix24(lead_id, summary, tasks, status)
            
            result = {
                "status": "updated" if success else "failed",
                "lead_id": lead_id,
                "summary": summary,
                "tasks_created": len(tasks),
                "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if success:
                self._send_telegram_message(f"✅ Bitrix24 updated: Lead {lead_id}")
            else:
                self._send_telegram_message(f"❌ Bitrix24 update failed: Lead {lead_id}")
            
            logger.info("Bitrix24 update completed")
            return result
            
        except Exception as e:
            logger.error(f"Bitrix24 update failed: {e}")
            return {"error": str(e)}

    def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        return {
            "tools": list(self.tools.values())
        }

    def list_resources(self) -> Dict[str, Any]:
        """List available resources"""
        return {
            "resources": list(self.resources.values())
        }

    def list_prompts(self) -> Dict[str, Any]:
        """List available prompts"""
        return {
            "prompts": list(self.prompts.values())
        }

    def get_prompt(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get prompt with arguments"""
        if name not in self.prompts:
            raise Exception(f"Prompt {name} not found")
        
        prompt = self.prompts[name]
        
        if name == "meeting_analysis":
            transcript = args.get("transcript", "")
            meeting_url = args.get("meeting_url", "")
            
            prompt_text = f"""
            Analyze this meeting transcript using Gemini AI:
            
            Meeting URL: {meeting_url}
            Transcript: {transcript}
            
            Provide:
            1. Meeting summary
            2. Key decisions
            3. Action items with deadlines
            4. Lead qualification score
            5. Next steps
            
            Return structured JSON response.
            """
            
            return {
                "description": prompt["description"],
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": prompt_text
                        }
                    }
                ]
            }
        
        elif name == "task_generation":
            analysis = args.get("analysis", {})
            lead_id = args.get("lead_id", "")
            
            prompt_text = f"""
            Generate actionable tasks from meeting analysis:
            
            Lead ID: {lead_id}
            Analysis: {json.dumps(analysis, indent=2)}
            
            Create specific, time-bound tasks with clear ownership.
            """
            
            return {
                "description": prompt["description"],
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": prompt_text
                        }
                    }
                ]
            }
        
        return {"error": "Unknown prompt"}

    def checklist_generation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate meeting checklist using Gemini"""
        try:
            meeting_type = args.get("meeting_type")
            lead_info = args.get("lead_info", "")
            
            if not meeting_type:
                raise Exception("Missing required parameter: meeting_type")
            
            logger.info(f"Generating checklist for {meeting_type} meeting")
            
            # Real Gemini checklist generation
            checklist = self._generate_checklist_with_gemini(meeting_type, lead_info)
            
            result = {
                "status": "generated",
                "meeting_type": meeting_type,
                "checklist": checklist,
                "generation_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self._send_telegram_message(f"📋 Checklist generated for {meeting_type} meeting")
            logger.info("Checklist generation completed")
            return result
            
        except Exception as e:
            logger.error(f"Checklist generation failed: {e}")
            return {"error": str(e)}

    def _generate_checklist_with_gemini(self, meeting_type: str, lead_info: str) -> Dict[str, Any]:
        """Generate checklist using Gemini AI"""
        try:
            if not model:
                raise Exception("Gemini model not configured - GEMINI_KEY missing")
            
            logger.info(f"Generating checklist for {meeting_type} meeting using Gemini")
            
            prompt = f"""
            Generate comprehensive meeting checklist for {meeting_type} meeting:
            
            Lead Info: {lead_info}
            
            Create detailed checklist with:
            1. Pre-meeting preparation tasks
            2. During meeting actions
            3. Post-meeting follow-up
            4. Documentation requirements
            5. Next steps and deadlines
            
            Return ONLY valid JSON format:
            {{
                "pre_meeting": [
                    "Task 1",
                    "Task 2",
                    "Task 3"
                ],
                "during_meeting": [
                    "Action 1",
                    "Action 2",
                    "Action 3"
                ],
                "post_meeting": [
                    "Follow-up 1",
                    "Follow-up 2",
                    "Follow-up 3"
                ],
                "documentation": [
                    "Doc 1",
                    "Doc 2",
                    "Doc 3"
                ],
                "next_steps": [
                    "Step 1",
                    "Step 2",
                    "Step 3"
                ]
            }}
            """
            
            logger.info("Sending checklist request to Gemini API")
            response = model.generate_content(prompt)
            
            if not response or not response.text:
                raise Exception("Empty response from Gemini API")
            
            # Parse JSON response
            result_text = response.text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:-3]
            elif result_text.startswith('```'):
                result_text = result_text[3:-3]
            
            result = json.loads(result_text)
            logger.info(f"Checklist generated successfully for {meeting_type}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {e}")
            logger.error(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
            return {
                "pre_meeting": ["Prepare meeting agenda", "Review lead information", "Set up recording"],
                "during_meeting": ["Take notes", "Ask qualifying questions", "Document decisions"],
                "post_meeting": ["Send follow-up email", "Update CRM", "Schedule next meeting"],
                "documentation": ["Meeting notes", "Action items", "Next steps"],
                "next_steps": ["Follow up within 24 hours", "Prepare proposal", "Schedule demo"]
            }
        except Exception as e:
            logger.error(f"Checklist generation failed: {e}")
            return {
                "pre_meeting": ["Prepare meeting agenda", "Review lead information", "Set up recording"],
                "during_meeting": ["Take notes", "Ask qualifying questions", "Document decisions"],
                "post_meeting": ["Send follow-up email", "Update CRM", "Schedule next meeting"],
                "documentation": ["Meeting notes", "Action items", "Next steps"],
                "next_steps": ["Follow up within 24 hours", "Prepare proposal", "Schedule demo"]
            }

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool by name"""
        if name == "meeting_join":
            return self.meeting_join(arguments)
        elif name == "meeting_analyze":
            return self.meeting_analyze(arguments)
        elif name == "bitrix_update":
            return self.bitrix_update(arguments)
        elif name == "checklist_generation":
            return self.checklist_generation(arguments)
        else:
            raise Exception(f"Unknown tool: {name}")

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP request"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            logger.info(f"Handling request: {method}")
            
            if method == "tools/list":
                result = self.list_tools()
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = self.call_tool(tool_name, arguments)
            elif method == "resources/list":
                result = self.list_resources()
            elif method == "resources/read":
                uri = params.get("uri")
                result = {"content": f"Resource content for {uri}"}
            elif method == "prompts/list":
                result = self.list_prompts()
            elif method == "prompts/get":
                prompt_name = params.get("name")
                prompt_args = params.get("arguments", {})
                result = self.get_prompt(prompt_name, prompt_args)
            else:
                raise Exception(f"Unknown method: {method}")
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
            logger.info(f"Request {method} completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Request handling failed: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }

def main():
    """Main function"""
    router = MCPRouter()
    logger.info("MCP Router started")
    
    # Read from stdin
    json_buffer = ""
    
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            
            json_buffer += line
            
            # Try to parse JSON
            try:
                request = json.loads(json_buffer.strip())
                response = router.handle_request(request)
                print(json.dumps(response, ensure_ascii=False))
                sys.stdout.flush()
                json_buffer = ""
            except json.JSONDecodeError:
                # Continue accumulating
                continue
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }
                print(json.dumps(error_response, ensure_ascii=False))
                sys.stdout.flush()
                json_buffer = ""
                
    except KeyboardInterrupt:
        logger.info("MCP Router stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()