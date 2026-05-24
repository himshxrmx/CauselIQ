"""
AI Incident Root Cause Analyzer — FastAPI Backend
Main application with CORS, routes, and in-memory incident store.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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

    try:
        analysis = analyze_incident(alert_data, logs)
        incidents_db[incident_id]["analysis"] = analysis
        incidents_db[incident_id]["status"] = "completed"
        incidents_db[incident_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
    except Exception as e:
        incidents_db[incident_id]["status"] = "failed"
        incidents_db[incident_id]["error"] = str(e)


# ─── Routes ──────────────────────────────────────────────

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
async def upload_logs(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload a raw log file for AI analysis."""
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
    
    return {"incident": incidents_db[incident_id], "message": f"Uploaded {len(lines)} lines of logs and completed AI analysis"}


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
