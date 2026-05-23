"""
AWS CloudWatch client for fetching logs around incident timestamps.
Uses the default boto3 session (assumes AWS CLI is configured).
"""

import boto3
from datetime import datetime, timedelta, timezone
from typing import Optional


def get_cloudwatch_client(region: Optional[str] = None):
    """Get a CloudWatch Logs client using default credentials."""
    kwargs = {}
    if region:
        kwargs["region_name"] = region
    return boto3.client("logs", **kwargs)


def list_log_groups(prefix: str = "", region: Optional[str] = None) -> list[dict]:
    """List available CloudWatch log groups, optionally filtered by prefix."""
    client = get_cloudwatch_client(region)
    kwargs = {}
    if prefix:
        kwargs["logGroupNamePrefix"] = prefix

    response = client.describe_log_groups(**kwargs)
    return [
        {
            "name": lg["logGroupName"],
            "storedBytes": lg.get("storedBytes", 0),
            "retentionDays": lg.get("retentionInDays", "Never expire"),
        }
        for lg in response.get("logGroups", [])
    ]


def fetch_cloudwatch_logs(
    log_group: str,
    start_time: datetime,
    end_time: datetime,
    filter_pattern: str = "",
    limit: int = 200,
    region: Optional[str] = None,
) -> list[dict]:
    """
    Fetch CloudWatch logs from a specific log group within a time window.

    Args:
        log_group: The CloudWatch log group name (e.g., "/aws/lambda/payment-api")
        start_time: Start of the time window (UTC datetime)
        end_time: End of the time window (UTC datetime)
        filter_pattern: CloudWatch filter pattern (optional)
        limit: Maximum number of log events to return
        region: AWS region override

    Returns:
        List of log event dicts with timestamp, message, and logStreamName
    """
    client = get_cloudwatch_client(region)

    # Convert to epoch milliseconds
    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)

    kwargs = {
        "logGroupName": log_group,
        "startTime": start_ms,
        "endTime": end_ms,
        "limit": limit,
        "interleaved": True,
    }
    if filter_pattern:
        kwargs["filterPattern"] = filter_pattern

    all_events = []
    try:
        response = client.filter_log_events(**kwargs)
        all_events.extend(response.get("events", []))

        # Paginate if needed (up to limit)
        while "nextToken" in response and len(all_events) < limit:
            kwargs["nextToken"] = response["nextToken"]
            response = client.filter_log_events(**kwargs)
            all_events.extend(response.get("events", []))

    except client.exceptions.ResourceNotFoundException:
        return [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": f"[ERROR] Log group '{log_group}' not found in CloudWatch.",
                "logStreamName": "system",
            }
        ]
    except Exception as e:
        return [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": f"[ERROR] Failed to fetch logs: {str(e)}",
                "logStreamName": "system",
            }
        ]

    # Format events
    formatted = []
    for event in all_events[:limit]:
        ts = event.get("timestamp", 0)
        formatted.append(
            {
                "timestamp": datetime.fromtimestamp(
                    ts / 1000, tz=timezone.utc
                ).isoformat(),
                "message": event.get("message", ""),
                "logStreamName": event.get("logStreamName", ""),
            }
        )

    return formatted


def build_time_window(
    timestamp_str: str, window_minutes: int = 15
) -> tuple[datetime, datetime]:
    """
    Build a time window around a given ISO timestamp.

    Returns (start_time, end_time) as UTC datetimes.
    """
    # Parse the timestamp
    ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    half_window = timedelta(minutes=window_minutes // 2)
    return ts - half_window, ts + half_window
