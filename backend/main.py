"""
AI Incident Root Cause Analyzer — FastAPI Backend
Main application with CORS, routes, and in-memory incident store.
"""

import uuid
import os
import asyncio
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from routellm.controller import Controller

from aws_client import fetch_cloudwatch_logs, build_time_window, list_log_groups
from ai_analyzer import analyze_incident
from mangum import Mangum

# ─── App Init ─────────────────────────────────────────────
app = FastAPI(
    title="AI Incident Root Cause Analyzer",
    version="1.0.0",
    description="SRE dashboard backend — fetches CloudWatch logs and uses Gemini AI to analyze incident root causes.",
)

# AWS Lambda Handler
handler = Mangum(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── RouteLLM Dual-Engine Setup ─────────────────────────────
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "gsk_pe1Q5sXAY_MASKED")

try:
    route_client = Controller(
        routers=["mf"],
        strong_model="gemini/gemini-2.5-pro",
        weak_model="groq/llama3-8b-8192"
    )
except Exception as e:
    print(f"Warning: RouteLLM Controller failed to initialize: {e}")
    route_client = None

# Mock Connectors (Replace with Boto3 and Git integrations)
async def fetch_aws_logs_mock(trace_id: str):
    await asyncio.sleep(0.2) # Simulate network latency
    return "TypeError: undefined property 'split' at data_parser.py:42"

async def fetch_git_code_mock(file_path: str, line_num: int):
    await asyncio.sleep(0.2) 
    return "39: def parse(data):\n40:     # No null check here\n41:     return data.split(',')"

# ─── In-Memory Store ──────────────────────────────────────
incidents_db: dict[str, dict] = {}


# ─── Models ───────────────────────────────────────────────
class AlertPayload(BaseModel):
    service: str = Field(..., description="Service name, e.g. 'payment-api'")
    timestamp: str = Field(..., description="ISO8601 timestamp of the alert")
    alert_type: str = Field(..., description="Type of alert, e.g. '5xx_errors'")
    description: str = Field(default="No description", description="Human-readable alert description")
    log_group: str = Field(default="", description="CloudWatch log group to query. If empty, defaults to /aws/ecs/{service}")
    region: str = Field(default="ap-south-1", description="AWS region")
    severity: str = Field(default="CRITICAL", description="Alert severity: CRITICAL, HIGH, MEDIUM, LOW")


class InvestigateRequest(BaseModel):
    incident_id: str


class SimulateRequest(BaseModel):
    scenario: str = Field(default="db_connection_failure", description="Scenario to simulate: db_connection_failure, oom_kill, deployment_rollback, cert_expiry, rate_limit")


# ─── Real AWS CloudWatch Scenarios ────────────────────────
# These use your actual log groups in us-east-1
REAL_SCENARIOS = {
    "the_grad_analyze": {
        "alert": {
            "service": "THE-GRAD-AnalyzeFunction",
            "timestamp": "2026-02-18T15:13:00Z",
            "alert_type": "lambda_error",
            "description": "Lambda AnalyzeFunction throwing GoogleGenerativeAI API errors — model not found",
            "log_group": "/aws/lambda/THE-GRAD-AnalyzeFunction-NPwt9WoH7iVX",
            "region": "us-east-1",
            "severity": "CRITICAL",
        },
    },
    "the_grad_records": {
        "alert": {
            "service": "THE-GRAD-GetRecordsFunction",
            "timestamp": "2026-02-18T17:09:00Z",
            "alert_type": "lambda_invocation",
            "description": "GetRecords Lambda function — check for invocation errors and cold starts",
            "log_group": "/aws/lambda/THE-GRAD-GetRecordsFunction-aHBjlC8bPeLD",
            "region": "us-east-1",
            "severity": "MEDIUM",
        },
    },
    "face_attendance": {
        "alert": {
            "service": "The-Face-AttendanceApiFunction",
            "timestamp": "2026-02-24T12:00:00Z",
            "alert_type": "api_error",
            "description": "Face Attendance API Lambda — investigating request failures and cold start issues",
            "log_group": "/aws/lambda/The-Face-AttendanceApiFunction-u1heB3YSMi0q",
            "region": "us-east-1",
            "severity": "HIGH",
        },
    },
    "sam_app_analyze": {
        "alert": {
            "service": "sam-app-AnalyzeFunction",
            "timestamp": "2026-02-18T12:58:00Z",
            "alert_type": "import_error",
            "description": "SAM App AnalyzeFunction failing on INIT — Runtime.ImportModuleError, cannot find module",
            "log_group": "/aws/lambda/sam-app-AnalyzeFunction-XZv6MSiuNj1T",
            "region": "us-east-1",
            "severity": "CRITICAL",
        },
    },
    "smart_attendance": {
        "alert": {
            "service": "smart-attendance-AttendanceApiFunction",
            "timestamp": "2026-02-22T06:00:00Z",
            "alert_type": "lambda_error",
            "description": "Smart Attendance API Lambda — investigating invocation patterns and errors",
            "log_group": "/aws/lambda/smart-attendance-stack-AttendanceApiFunction-mPJIb78NeGqf",
            "region": "us-east-1",
            "severity": "HIGH",
        },
    },
}


def _run_investigation(incident_id: str):
    """Background task to run AI analysis on an incident."""
    incident = incidents_db.get(incident_id)
    if not incident:
        return

    incidents_db[incident_id]["status"] = "analyzing"

    alert_data = incident["alert"]
    logs = incident.get("raw_logs", [])
    source_code = incident.get("source_code")

    try:
        analysis = analyze_incident(alert_data, logs, source_code=source_code)
        incidents_db[incident_id]["analysis"] = analysis
        incidents_db[incident_id]["status"] = "completed"
        incidents_db[incident_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
    except Exception as e:
        incidents_db[incident_id]["status"] = "failed"
        incidents_db[incident_id]["error"] = str(e)


# ─── Routes ──────────────────────────────────────────────

@app.post("/webhook/cloudwatch-alert")
async def handle_incident_webhook(payload: dict):
    """The High-Speed Webhook Endpoint using RouteLLM adaptive routing."""
    if not route_client:
        raise HTTPException(status_code=500, detail="RouteLLM not initialized")
        
    trace_id = payload.get("trace_id", "unknown")
    
    # Execute the log fetch and code fetch simultaneously
    logs_task = fetch_aws_logs_mock(trace_id)
    code_task = fetch_git_code_mock("data_parser.py", 42)
    
    raw_logs, source_code = await asyncio.gather(logs_task, code_task)
    
    # Build the Synthesis Prompt
    synthesis_prompt = f"""
    You are the CauseIQ Agent.
    AWS CLOUDWATCH LOG: {raw_logs}
    SOURCE CODE WINDOW: {source_code}
    
    Identify the exact bug and output the required code fix.
    Output a strict JSON schema containing {{"is_anomaly": true, "root_cause": "...", "remediation_steps": "..."}}.
    """
    
    # RouteLLM automatically calculates complexity. 
    # The '0.11593' threshold sends simple bugs to Groq and hard bugs to Gemini.
    response = route_client.chat.completions.create(
        model="router-mf-0.11593",
        messages=[{"role": "user", "content": synthesis_prompt}]
    )
    
    return {
        "status": "success", 
        "resolution": response.choices[0].message.content
    }

@app.get("/")
def root():
    return {"status": "operational", "app": "AI Incident Root Cause Analyzer", "version": "1.0.0"}


@app.get("/api/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/alerts")
def get_alerts():
    """Get all incidents, sorted by most recent."""
    sorted_incidents = sorted(
        incidents_db.values(),
        key=lambda x: x.get("created_at", ""),
        reverse=True,
    )
    # Return without raw_logs to keep payload small
    return [
        {k: v for k, v in inc.items() if k not in ("raw_logs",)}
        for inc in sorted_incidents
    ]


@app.get("/api/alerts/{incident_id}")
def get_alert(incident_id: str):
    """Get a specific incident with full details including raw logs."""
    incident = incidents_db.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.post("/api/webhook")
def receive_alert(payload: AlertPayload, background_tasks: BackgroundTasks):
    """
    Receive an alert webhook, fetch CloudWatch logs, and trigger AI analysis.
    This is the primary entry point for real alerts.
    """
    incident_id = str(uuid.uuid4())[:8]
    log_group = payload.log_group or f"/aws/lambda/{payload.service}"

    # Build time window
    start_time, end_time = build_time_window(payload.timestamp, window_minutes=15)

    # Fetch real CloudWatch logs
    raw_logs = fetch_cloudwatch_logs(
        log_group=log_group,
        start_time=start_time,
        end_time=end_time,
        region=payload.region,
    )

    incident = {
        "id": incident_id,
        "alert": payload.model_dump(),
        "raw_logs": raw_logs,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "analysis": None,
        "error": None,
    }

    incidents_db[incident_id] = incident

    # Run AI analysis synchronously for Lambda
    _run_investigation(incident_id)

    return {"incident": incidents_db[incident_id], "message": "Investigation completed"}


@app.post("/api/simulate")
def simulate_incident(req: SimulateRequest, background_tasks: BackgroundTasks):
    """
    Trigger an investigation using a REAL AWS CloudWatch log group.
    Fetches actual logs from your AWS account and sends them to Gemini.
    """
    scenario = REAL_SCENARIOS.get(req.scenario)
    if not scenario:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario '{req.scenario}'. Available: {list(REAL_SCENARIOS.keys())}",
        )

    incident_id = str(uuid.uuid4())[:8]
    alert_data = scenario["alert"]

    # Fetch REAL logs from AWS CloudWatch — wide window to capture all events
    start_time, end_time = build_time_window(alert_data["timestamp"], window_minutes=120)

    raw_logs = fetch_cloudwatch_logs(
        log_group=alert_data["log_group"],
        start_time=start_time,
        end_time=end_time,
        region=alert_data.get("region", "us-east-1"),
        limit=200,
    )

    incident = {
        "id": incident_id,
        "alert": alert_data,
        "raw_logs": raw_logs,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "analysis": None,
        "error": None,
    }

    incidents_db[incident_id] = incident
    
    # Run AI analysis synchronously for Lambda
    _run_investigation(incident_id)

    return {"incident": incidents_db[incident_id], "scenario": req.scenario, "message": f"Fetched {len(raw_logs)} logs and completed AI analysis"}


@app.post("/api/upload")
async def upload_logs(background_tasks: BackgroundTasks, file: UploadFile = File(...), code_file: UploadFile = File(None)):
    """Upload a raw log file and optional source code for AI analysis."""
    incident_id = str(uuid.uuid4())[:8]
    
    content = await file.read()
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be a valid UTF-8 text file.")
        
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    # Limit to 500 lines to prevent overwhelming the AI
    if len(lines) > 500:
        lines = lines[-500:]

    raw_logs = [{"timestamp": "N/A", "logStreamName": file.filename, "message": line} for line in lines]
    
    alert_data = {
        "service": file.filename or "uploaded_file",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alert_type": "custom_upload",
        "description": "User uploaded log file for AI analysis",
        "region": "local",
        "severity": "HIGH",
    }
    
    source_code = None
    if code_file:
        code_content = await code_file.read()
        try:
            source_code = code_content.decode('utf-8')
            # Limit source code length to prevent overwhelming the AI
            if len(source_code) > 20000:
                source_code = source_code[:20000] + "\n...[TRUNCATED]"
        except UnicodeDecodeError:
            pass  # If code isn't UTF-8, just ignore it
            
    incident = {
        "id": incident_id,
        "alert": alert_data,
        "raw_logs": raw_logs,
        "source_code": source_code,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "analysis": None,
        "error": None,
    }
    
    incidents_db[incident_id] = incident
    
    # Run AI analysis synchronously for Lambda
    _run_investigation(incident_id)
    
    msg = f"Uploaded {len(lines)} lines of logs"
    if source_code:
        msg += " and source code"
    msg += " and completed AI analysis"
    
    return {"incident": incidents_db[incident_id], "message": msg}


@app.get("/api/scenarios")
def list_scenarios():
    """List available simulation scenarios."""
    return {
        name: {
            "service": data["alert"]["service"],
            "alert_type": data["alert"]["alert_type"],
            "severity": data["alert"]["severity"],
            "description": data["alert"]["description"],
        }
        for name, data in REAL_SCENARIOS.items()
    }


@app.get("/api/log-groups")
def get_log_groups(prefix: str = ""):
    """List CloudWatch log groups (requires valid AWS credentials)."""
    try:
        groups = list_log_groups(prefix=prefix)
        return {"log_groups": groups}
    except Exception as e:
        return {"log_groups": [], "error": str(e)}


@app.get("/api/stats")
def get_stats():
    """Dashboard statistics."""
    total = len(incidents_db)
    completed = sum(1 for i in incidents_db.values() if i["status"] == "completed")
    analyzing = sum(1 for i in incidents_db.values() if i["status"] == "analyzing")
    failed = sum(1 for i in incidents_db.values() if i["status"] == "failed")

    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    category_counts = {}
    avg_confidence = 0
    confidence_list = []

    for inc in incidents_db.values():
        sev = inc.get("alert", {}).get("severity", "MEDIUM")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

        if inc.get("analysis"):
            cat = inc["analysis"].get("root_cause_category", "UNKNOWN")
            category_counts[cat] = category_counts.get(cat, 0) + 1
            confidence_list.append(inc["analysis"].get("confidence_score", 0))

    if confidence_list:
        avg_confidence = sum(confidence_list) / len(confidence_list)

    return {
        "total_incidents": total,
        "completed": completed,
        "analyzing": analyzing,
        "failed": failed,
        "severity_breakdown": severity_counts,
        "category_breakdown": category_counts,
        "avg_confidence": round(avg_confidence, 2),
    }
