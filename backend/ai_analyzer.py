"""
CauseIQ Multi-Agent AI Analyzer
================================
3-phase orchestration pipeline using Google Gemini for deep incident root cause analysis.

Phase 1 (Agent 1 — Log Diagnostician): Triage logs, classify system state, extract error context.
Phase 2 (Agent 2 — Code & Config Analyst): Analyze code/config patterns against Agent 1's findings.
Phase 3 (Agent 3 — Synthesizer): Merge both analyses into a final RCA report with hotfix suggestion.
"""

import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

_client = None
MODEL_ID = "gemini-2.5-flash"


def _get_client() -> genai.Client:
    """Get or create the GenAI client."""
    global _client
    if _client is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set. Add it to backend/.env file.")
        _client = genai.Client(api_key=api_key)
    return _client


def _parse_response(text: str) -> dict:
    """Strip markdown fences and parse JSON from Gemini response."""
    if text.startswith("```json"):
        text = text.strip("`").removeprefix("json").strip()
    elif text.startswith("```"):
        text = text.strip("`").strip()
    return json.loads(text)


def _format_logs(raw_logs: list[dict]) -> str:
    """Format raw log dicts into readable text for prompts."""
    return "\n".join(
        f"[{log.get('timestamp', 'N/A')}] [{log.get('logStreamName', 'N/A')}] {log.get('message', '')}"
        for log in raw_logs
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AGENT 1 — The Telemetry & Log Diagnostician
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AGENT_1_SYSTEM = """You are CauseIQ's Level 1 Site Reliability Engineer (Log Diagnostician). Your objective is to parse raw application and infrastructure logs to determine the health of the system.

Instructions:
1. CLASSIFY: Analyze the provided logs and classify the system state as exactly "CORRECT" (normal operations/warnings only) or "WRONG" (fatal errors, exceptions, configuration blockages, crashes).
2. EXTRACT: If the state is "WRONG", extract the following from the stack trace or error message:
   - Error Type (e.g., NullPointerException, ImportModuleError, AccessDenied, OOMKilled)
   - Failing Filepath: The exact file where the error originated (if visible in logs/stack trace)
   - Line Number: The exact line number of the failure (if visible)
   - Involved Variables: Any missing or malformed data mentioned in the log
   - Error Patterns: List of distinct error patterns found (e.g., repeated connection refused, timeout spikes)
3. SUMMARIZE: Write a brief diagnostic summary explaining what the logs reveal.

Output ONLY a strict JSON object. Do not include markdown formatting or conversational text."""

AGENT_1_SCHEMA = types.Schema(
    type="OBJECT",
    properties={
        "status": types.Schema(
            type="STRING",
            description="System health classification.",
            enum=["CORRECT", "WRONG"],
        ),
        "confidence_score": types.Schema(
            type="NUMBER",
            description="Confidence in the classification (0.0 to 1.0).",
        ),
        "diagnostic_summary": types.Schema(
            type="STRING",
            description="Brief summary of what the logs reveal about the system state.",
        ),
        "extracted_context": types.Schema(
            type="OBJECT",
            description="Error context extracted from logs. Empty object if status is CORRECT.",
            properties={
                "error_type": types.Schema(type="STRING", description="The primary error type/exception class."),
                "filepath": types.Schema(type="STRING", description="File path where error originated. 'unknown' if not visible."),
                "line_number": types.Schema(type="INTEGER", description="Line number of failure. 0 if not visible."),
                "variables": types.Schema(
                    type="ARRAY",
                    items=types.Schema(type="STRING"),
                    description="Missing/malformed variables or configs mentioned in errors.",
                ),
                "error_patterns": types.Schema(
                    type="ARRAY",
                    items=types.Schema(type="STRING"),
                    description="Distinct error patterns found across all log entries.",
                ),
            },
            required=["error_type", "filepath", "line_number", "variables", "error_patterns"],
        ),
    },
    required=["status", "confidence_score", "diagnostic_summary", "extracted_context"],
)


def agent_1_log_diagnostician(raw_logs: list[dict]) -> dict:
    """Phase 1: Triage raw logs and extract error context."""
    log_text = _format_logs(raw_logs)

    prompt = f"""## RAW LOGS ({len(raw_logs)} events)
```
{log_text if log_text.strip() else '[No logs available]'}
```

Analyze these logs. Classify the system state and extract all error context."""

    response = _get_client().models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=AGENT_1_SYSTEM,
            response_mime_type="application/json",
            response_schema=AGENT_1_SCHEMA,
            temperature=0.1,
            max_output_tokens=2048,
        ),
    )
    return _parse_response(response.text)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AGENT 2 — The Codebase & Config Analyst
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AGENT_2_SYSTEM = """You are CauseIQ's Senior Software & Cloud Architect. The Log Diagnostician has identified a critical failure. Your job is to analyze the error context, code patterns visible in the logs, and infrastructure configuration to determine WHY the logic failed.

Instructions:
1. CORRELATE: Match the error from the logs to the likely code/config defect.
2. INVESTIGATE: Based on the error type and patterns, determine if this is a code bug, a configuration issue, a deployment problem, or an infrastructure failure.
3. DETERMINE ROOT CAUSE: Write a precise, technical explanation of what went wrong at the code/config level.
4. DRAFT FIX: Write the exact code changes or configuration commands needed to resolve the issue. If you can identify the failing file, write a unified diff patch.

Be specific. Reference exact error types, module names, and config keys from the provided context."""

AGENT_2_SCHEMA = types.Schema(
    type="OBJECT",
    properties={
        "root_cause": types.Schema(
            type="STRING",
            description="Technical explanation of WHY the code/config failed at a structural level.",
        ),
        "root_cause_category": types.Schema(
            type="STRING",
            description="Category of the root cause.",
            enum=[
                "DEPLOYMENT", "CONFIGURATION", "RESOURCE_EXHAUSTION",
                "DEPENDENCY_FAILURE", "NETWORK", "SECURITY",
                "CODE_BUG", "INFRASTRUCTURE", "UNKNOWN",
            ],
        ),
        "code_analysis": types.Schema(
            type="STRING",
            description="Analysis of the code-level defect. Reference specific modules, functions, or config keys.",
        ),
        "config_analysis": types.Schema(
            type="STRING",
            description="Analysis of any infrastructure/configuration issues (IAM, env vars, security groups, etc.).",
        ),
        "suggested_fix": types.Schema(
            type="STRING",
            description="The exact code change, config update, or CLI command to fix the issue.",
        ),
        "hotfix_diff": types.Schema(
            type="STRING",
            description="A unified git diff patch for the fix, if applicable. Empty string if not applicable.",
        ),
    },
    required=["root_cause", "root_cause_category", "code_analysis", "config_analysis", "suggested_fix", "hotfix_diff"],
)


def agent_2_code_analyst(agent_1_output: dict, alert_data: dict, raw_logs: list[dict], source_code: str | None = None) -> dict:
    """Phase 2: Deep code/config analysis using Agent 1's findings."""
    log_text = _format_logs(raw_logs)
    ctx = agent_1_output.get("extracted_context", {})

    source_code_section = ""
    if source_code:
        source_code_section = f"""\n## UPLOADED SOURCE CODE\n```\n{source_code[:10000]}\n```\n"""

    prompt = f"""## AGENT 1 DIAGNOSTIC FINDINGS
- **System Status:** {agent_1_output.get('status', 'UNKNOWN')}
- **Confidence:** {agent_1_output.get('confidence_score', 0)}
- **Summary:** {agent_1_output.get('diagnostic_summary', 'N/A')}
- **Error Type:** {ctx.get('error_type', 'N/A')}
- **Failing File:** {ctx.get('filepath', 'unknown')}
- **Line Number:** {ctx.get('line_number', 0)}
- **Involved Variables:** {', '.join(ctx.get('variables', [])) or 'N/A'}
- **Error Patterns:** {', '.join(ctx.get('error_patterns', [])) or 'N/A'}

## ALERT CONTEXT
- **Service:** {alert_data.get('service', 'unknown')}
- **Alert Type:** {alert_data.get('alert_type', 'unknown')}
- **Description:** {alert_data.get('description', 'N/A')}
- **Region:** {alert_data.get('region', 'us-east-1')}
- **Severity:** {alert_data.get('severity', 'UNKNOWN')}{source_code_section}

## RAW LOGS (for reference, {len(raw_logs)} events)
```
{log_text[:3000] if log_text.strip() else '[No logs]'}
```

Using the Log Diagnostician's findings and the raw evidence, determine the structural root cause at the code and configuration level. Provide a precise fix."""

    response = _get_client().models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=AGENT_2_SYSTEM,
            response_mime_type="application/json",
            response_schema=AGENT_2_SCHEMA,
            temperature=0.2,
            max_output_tokens=3072,
        ),
    )
    return _parse_response(response.text)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AGENT 3 — The Synthesizer & Report Generator
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AGENT_3_SYSTEM = """You are CauseIQ's Lead DevOps AI — the final layer of the RCA pipeline. You will receive diagnostic data from the Log Agent (Phase 1) and structural analysis from the Code Agent (Phase 2).

Your Task: Synthesize both analyses into a highly readable, actionable Incident Report for an engineering team.

Instructions:
1. EXECUTIVE SUMMARY: Write a clear 2-3 sentence explanation of what broke and why, in plain English that a VP of Engineering would understand.
2. EVIDENCE MAPPING: Explain how the log anomaly maps to the code/config defect.
3. IMPACT ASSESSMENT: Determine the blast radius — affected users, downstream services, and business impact.
4. TIMELINE: Reconstruct the chronological sequence of events leading to the failure.
5. REMEDIATION: Provide step-by-step actionable instructions with exact CLI commands.
6. CONFIDENCE: Provide a final confidence score that accounts for both agents' certainty levels.

Your output must be the definitive, final incident report."""

AGENT_3_SCHEMA = types.Schema(
    type="OBJECT",
    properties={
        "probable_cause": types.Schema(
            type="STRING",
            description="Executive summary: clear explanation of what went wrong, referencing specific evidence.",
        ),
        "confidence_score": types.Schema(
            type="NUMBER",
            description="Final confidence score (0.0 to 1.0), weighted from both agent analyses.",
        ),
        "severity": types.Schema(
            type="STRING",
            description="Final incident severity.",
            enum=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        ),
        "impact_analysis": types.Schema(
            type="STRING",
            description="Blast radius: affected users, services, and business impact.",
        ),
        "actionable_remediation": types.Schema(
            type="ARRAY",
            items=types.Schema(
                type="OBJECT",
                properties={
                    "step": types.Schema(type="INTEGER", description="Step number."),
                    "action": types.Schema(type="STRING", description="Description of the action."),
                    "command": types.Schema(type="STRING", description="Exact CLI command. Empty if N/A."),
                },
                required=["step", "action", "command"],
            ),
            description="Ordered remediation steps with executable commands.",
        ),
        "root_cause_category": types.Schema(
            type="STRING",
            description="Final root cause category.",
            enum=[
                "DEPLOYMENT", "CONFIGURATION", "RESOURCE_EXHAUSTION",
                "DEPENDENCY_FAILURE", "NETWORK", "SECURITY",
                "CODE_BUG", "INFRASTRUCTURE", "UNKNOWN",
            ],
        ),
        "timeline": types.Schema(
            type="ARRAY",
            items=types.Schema(
                type="OBJECT",
                properties={
                    "time": types.Schema(type="STRING", description="Timestamp or relative time."),
                    "event": types.Schema(type="STRING", description="What happened."),
                },
                required=["time", "event"],
            ),
            description="Chronological timeline of the incident cascade.",
        ),
    },
    required=[
        "probable_cause", "confidence_score", "severity",
        "impact_analysis", "actionable_remediation", "root_cause_category", "timeline",
    ],
)


def agent_3_synthesizer(agent_1_output: dict, agent_2_output: dict, alert_data: dict) -> dict:
    """Phase 3: Synthesize both agent outputs into the final RCA report."""

    prompt = f"""## PHASE 1 — LOG DIAGNOSTICIAN FINDINGS
- **System Status:** {agent_1_output.get('status', 'UNKNOWN')}
- **Log Confidence:** {agent_1_output.get('confidence_score', 0)}
- **Diagnostic Summary:** {agent_1_output.get('diagnostic_summary', 'N/A')}
- **Error Type:** {agent_1_output.get('extracted_context', {}).get('error_type', 'N/A')}
- **Failing File:** {agent_1_output.get('extracted_context', {}).get('filepath', 'N/A')}
- **Error Patterns:** {', '.join(agent_1_output.get('extracted_context', {}).get('error_patterns', []))}

## PHASE 2 — CODE & CONFIG ANALYST FINDINGS
- **Root Cause:** {agent_2_output.get('root_cause', 'N/A')}
- **Category:** {agent_2_output.get('root_cause_category', 'UNKNOWN')}
- **Code Analysis:** {agent_2_output.get('code_analysis', 'N/A')}
- **Config Analysis:** {agent_2_output.get('config_analysis', 'N/A')}
- **Suggested Fix:** {agent_2_output.get('suggested_fix', 'N/A')}

## ORIGINAL ALERT CONTEXT
- **Service:** {alert_data.get('service', 'unknown')}
- **Timestamp:** {alert_data.get('timestamp', 'unknown')}
- **Alert Type:** {alert_data.get('alert_type', 'unknown')}
- **Description:** {alert_data.get('description', 'N/A')}
- **Region:** {alert_data.get('region', 'us-east-1')}
- **Severity:** {alert_data.get('severity', 'UNKNOWN')}

Synthesize the findings from both agents into a definitive incident report. Your confidence score should reflect the combined certainty of both analyses."""

    response = _get_client().models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=AGENT_3_SYSTEM,
            response_mime_type="application/json",
            response_schema=AGENT_3_SCHEMA,
            temperature=0.2,
            max_output_tokens=4096,
        ),
    )
    return _parse_response(response.text)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ORCHESTRATOR — Multi-Agent Pipeline
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_multi_agent_pipeline(alert_payload: dict, raw_logs: list[dict], source_code: str | None = None) -> dict:
    """
    Execute the full 3-phase multi-agent RCA pipeline.

    Returns the final analysis dict (backward-compatible with the old single-agent schema)
    plus additional multi-agent metadata in 'agent_phases'.
    """

    # ── Phase 1: Log Diagnostician ──
    agent_1_result = agent_1_log_diagnostician(raw_logs)

    # If system is CORRECT, short-circuit with a clean report
    if agent_1_result.get("status") == "CORRECT":
        return {
            "probable_cause": "No critical issues detected. System appears to be operating normally.",
            "confidence_score": agent_1_result.get("confidence_score", 0.9),
            "severity": "LOW",
            "impact_analysis": "No measurable impact. Logs show normal operational patterns with no errors or anomalies.",
            "actionable_remediation": [
                {"step": 1, "action": "No action required. Continue monitoring.", "command": ""}
            ],
            "root_cause_category": "UNKNOWN",
            "timeline": [
                {"time": alert_payload.get("timestamp", "N/A"), "event": "Alert received — logs analyzed — no issues found."}
            ],
            "agent_phases": {
                "log_diagnostician": agent_1_result,
                "code_analyst": None,
            },
            "hotfix_diff": "",
        }

    # ── Phase 2: Code & Config Analyst ──
    agent_2_result = agent_2_code_analyst(agent_1_result, alert_payload, raw_logs, source_code=source_code)

    # ── Phase 3: Synthesizer ──
    final_report = agent_3_synthesizer(agent_1_result, agent_2_result, alert_payload)

    # Attach multi-agent metadata to the final report
    final_report["agent_phases"] = {
        "log_diagnostician": agent_1_result,
        "code_analyst": {
            "root_cause": agent_2_result.get("root_cause", ""),
            "code_analysis": agent_2_result.get("code_analysis", ""),
            "config_analysis": agent_2_result.get("config_analysis", ""),
            "suggested_fix": agent_2_result.get("suggested_fix", ""),
        },
    }
    final_report["hotfix_diff"] = agent_2_result.get("hotfix_diff", "")

    return final_report


# Keep backward-compatible function name
def analyze_incident(alert_payload: dict, raw_logs: list[dict], source_code: str | None = None) -> dict:
    """Backward-compatible wrapper that runs the full multi-agent pipeline."""
    return run_multi_agent_pipeline(alert_payload, raw_logs, source_code=source_code)
