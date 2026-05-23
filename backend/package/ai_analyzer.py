"""
AI Analyzer using Google GenAI SDK (Gemini) for incident root cause analysis.
Enforces structured JSON output via response_schema.
"""

import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Lazy-initialized GenAI client (so the module can import without a key)
_client = None

# The model to use — latest Gemini Flash
MODEL_ID = "gemini-2.5-flash"


def _get_client() -> genai.Client:
    """Get or create the GenAI client, raising a clear error if no API key."""
    global _client
    if _client is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not set. Add it to backend/.env file."
            )
        _client = genai.Client(api_key=api_key)
    return _client

# System prompt for SRE-focused root cause analysis
SYSTEM_PROMPT = """You are an elite Site Reliability Engineer (SRE) AI assistant specializing in incident root cause analysis. You analyze cloud infrastructure logs, metrics, and alert payloads to determine the root cause of production incidents.

Your analysis must be:
1. PRECISE — Identify the exact component, service, or configuration that failed.
2. EVIDENCE-BASED — Reference specific log lines, error codes, or patterns from the provided logs.
3. ACTIONABLE — Provide concrete remediation steps with exact commands (AWS CLI, kubectl, etc.).
4. SEVERITY-AWARE — Assess the blast radius and business impact accurately.

When analyzing logs, look for:
- Error patterns (5xx status codes, timeout errors, connection refused)
- Resource exhaustion (OOM kills, CPU throttling, disk full)
- Configuration issues (mismatched env vars, wrong endpoints, expired certs)
- Dependency failures (database connection errors, upstream service failures)
- Deployment-related issues (bad deployments, version mismatches)

Always provide your confidence score as a float between 0.0 and 1.0."""


# Define the response schema for structured output
RESPONSE_SCHEMA = types.Schema(
    type="OBJECT",
    properties={
        "probable_cause": types.Schema(
            type="STRING",
            description="A clear, concise explanation of what went wrong in plain English. Reference specific log evidence.",
        ),
        "confidence_score": types.Schema(
            type="NUMBER",
            description="Confidence score between 0.0 and 1.0 indicating how certain the analysis is.",
        ),
        "severity": types.Schema(
            type="STRING",
            description="Incident severity: CRITICAL, HIGH, MEDIUM, or LOW.",
            enum=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        ),
        "impact_analysis": types.Schema(
            type="STRING",
            description="Assessment of blast radius, affected users/services, and business impact.",
        ),
        "actionable_remediation": types.Schema(
            type="ARRAY",
            items=types.Schema(
                type="OBJECT",
                properties={
                    "step": types.Schema(
                        type="INTEGER", description="Step number in the remediation sequence."
                    ),
                    "action": types.Schema(
                        type="STRING",
                        description="Description of the remediation action.",
                    ),
                    "command": types.Schema(
                        type="STRING",
                        description="The exact CLI command to execute (AWS CLI, kubectl, etc.). Leave empty if no command is needed.",
                    ),
                },
                required=["step", "action", "command"],
            ),
            description="Ordered list of remediation steps with executable commands.",
        ),
        "root_cause_category": types.Schema(
            type="STRING",
            description="Category of the root cause.",
            enum=[
                "DEPLOYMENT",
                "CONFIGURATION",
                "RESOURCE_EXHAUSTION",
                "DEPENDENCY_FAILURE",
                "NETWORK",
                "SECURITY",
                "CODE_BUG",
                "INFRASTRUCTURE",
                "UNKNOWN",
            ],
        ),
        "timeline": types.Schema(
            type="ARRAY",
            items=types.Schema(
                type="OBJECT",
                properties={
                    "time": types.Schema(
                        type="STRING", description="ISO timestamp or relative time."
                    ),
                    "event": types.Schema(
                        type="STRING", description="What happened at this time."
                    ),
                },
                required=["time", "event"],
            ),
            description="Reconstructed timeline of events leading to the incident.",
        ),
    },
    required=[
        "probable_cause",
        "confidence_score",
        "severity",
        "impact_analysis",
        "actionable_remediation",
        "root_cause_category",
        "timeline",
    ],
)


def analyze_incident(
    alert_payload: dict,
    raw_logs: list[dict],
) -> dict:
    """
    Send alert context and raw logs to Gemini for root cause analysis.

    Args:
        alert_payload: The incoming alert data (service, timestamp, alert_type, etc.)
        raw_logs: List of CloudWatch log events

    Returns:
        Structured analysis dict with probable_cause, confidence_score, etc.
    """
    # Format logs for the prompt
    log_text = "\n".join(
        [
            f"[{log.get('timestamp', 'N/A')}] [{log.get('logStreamName', 'N/A')}] {log.get('message', '')}"
            for log in raw_logs
        ]
    )

    user_prompt = f"""## INCIDENT ALERT
- **Service:** {alert_payload.get('service', 'unknown')}
- **Timestamp:** {alert_payload.get('timestamp', 'unknown')}
- **Alert Type:** {alert_payload.get('alert_type', 'unknown')}
- **Description:** {alert_payload.get('description', 'No description provided')}
- **Region:** {alert_payload.get('region', 'us-east-1')}

## RAW CLOUDWATCH LOGS ({len(raw_logs)} events)
```
{log_text if log_text.strip() else '[No logs available — log group may not exist or no events in the time window]'}
```

Analyze these logs and the alert context. Determine the root cause, assess impact, and provide actionable remediation steps with exact commands."""

    response = _get_client().models.generate_content(
        model=MODEL_ID,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
            temperature=0.2,
            max_output_tokens=4096,
        ),
    )

    # Parse the structured JSON response
    text = response.text
    if text.startswith("```json"):
        text = text.strip("`").removeprefix("json").strip()
    elif text.startswith("```"):
        text = text.strip("`").strip()
        
    result = json.loads(text)
    return result


def analyze_with_mock_logs() -> dict:
    """Test function using mock log data to verify the AI pipeline works."""
    mock_alert = {
        "service": "payment-api",
        "timestamp": "2026-05-23T10:00:00Z",
        "alert_type": "5xx_errors",
        "description": "Spike in 5xx error rate exceeding 15% threshold",
        "region": "ap-south-1",
    }

    mock_logs = [
        {
            "timestamp": "2026-05-23T09:55:12Z",
            "logStreamName": "payment-api/prod/i-0abc123",
            "message": "INFO: Deployment v2.4.1 started - image: payment-api:2.4.1-rc3",
        },
        {
            "timestamp": "2026-05-23T09:56:30Z",
            "logStreamName": "payment-api/prod/i-0abc123",
            "message": "INFO: Health check passed on port 8080",
        },
        {
            "timestamp": "2026-05-23T09:58:45Z",
            "logStreamName": "payment-api/prod/i-0abc123",
            "message": "ERROR: Connection refused to payments-db.internal:5432 - max retries exhausted (3/3)",
        },
        {
            "timestamp": "2026-05-23T09:59:01Z",
            "logStreamName": "payment-api/prod/i-0abc123",
            "message": "ERROR: sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server: Connection refused",
        },
        {
            "timestamp": "2026-05-23T09:59:15Z",
            "logStreamName": "payment-api/prod/i-0abc123",
            "message": "CRITICAL: Circuit breaker OPEN for payments-db - 95% failure rate in last 30s",
        },
        {
            "timestamp": "2026-05-23T09:59:30Z",
            "logStreamName": "payment-api/prod/i-0abc123",
            "message": "ERROR: POST /api/v2/charge returned 503 - upstream_connect_error",
        },
        {
            "timestamp": "2026-05-23T10:00:00Z",
            "logStreamName": "payment-api/prod/i-0abc123",
            "message": "ALERT: 5xx error rate at 47.3% (threshold: 15%) - PagerDuty triggered",
        },
        {
            "timestamp": "2026-05-23T10:00:15Z",
            "logStreamName": "payment-api/prod/i-0def456",
            "message": "ERROR: RDS instance payments-db showing status: storage-full, allocated: 100GB, used: 99.8GB",
        },
        {
            "timestamp": "2026-05-23T10:01:00Z",
            "logStreamName": "payment-api/prod/i-0abc123",
            "message": "WARN: Fallback cache returning stale data for payment tokens - last refresh 45min ago",
        },
        {
            "timestamp": "2026-05-23T10:02:30Z",
            "logStreamName": "payment-api/prod/i-0abc123",
            "message": "ERROR: POST /api/v2/refund returned 500 - NoneType has no attribute 'transaction_id'",
        },
    ]

    return analyze_incident(mock_alert, mock_logs)
