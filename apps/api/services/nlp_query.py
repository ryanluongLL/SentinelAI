import re
import anthropic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from core.config import settings

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

SCHEMA_CONTEXT = """
You are a PostgreSQL expert for a cybersecurity threat detection system called SentinelAI.
Convert the user's natural language question into a valid PostgreSQL SELECT query.

Database schema:

Table: network_events
- id (UUID)
- timestamp (TIMESTAMPTZ)
- source_ip (INET)
- destination_ip (INET)
- source_port (INTEGER)
- destination_port (INTEGER)
- protocol (VARCHAR)
- bytes_transferred (BIGINT)
- packet_count (INTEGER)
- duration_ms (FLOAT)
- flags (JSONB)
- raw_payload (TEXT)

Table: threats
- id (UUID)
- detected_at (TIMESTAMPTZ)
- threat_type (VARCHAR) - values: ddos, port_scan, malware, brute_force, anomaly
- severity (VARCHAR) - values: low, medium, high, critical
- confidence_score (FLOAT) - between 0 and 1
- source_ip (INET)
- description (TEXT)
- is_resolved (BOOLEAN)
- resolved_at (TIMESTAMPTZ)
- metadata (JSONB)

Table: alerts
- id (UUID)
- threat_id (UUID)
- created_at (TIMESTAMPTZ)
- is_read (BOOLEAN)
- message (TEXT)

Rules you must follow:
1. Only return the raw SQL query, no explanation, no markdown, no backticks
2. Only generate SELECT statements, never INSERT, UPDATE, DELETE, DROP, TRUNCATE, or ALTER
3. Always add LIMIT 100 unless the user specifies otherwise
4. Always cast IP addresses with ::text in SELECT clauses
5. Always cast UUIDs with ::text in SELECT clauses
6. Use NOW() for current time references
7. If the question is ambiguous, write the most reasonable query
8. If the question cannot be answered with the available schema, return exactly: INVALID_QUERY
"""

BLOCKED_KEYWORDS = [
    "insert", "update", "delete", "drop", "truncate",
    "alter", "create", "grant", "revoke", "exec",
    "execute", "pg_", "information_schema"
]

def is_safe_query(sql: str) -> bool:
    sql_lower = sql.lower().strip()

    if not sql_lower.startswith("select"):
        return False

    for keyword in BLOCKED_KEYWORDS:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, sql_lower):
            return False

    return True

def generate_sql(question: str) -> str:
    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": f"{SCHEMA_CONTEXT}\n\nUser question: {question}"
            }
        ]
    )

    sql = message.content[0].text.strip()
    sql = re.sub(r'```sql\s*', '', sql)
    sql = re.sub(r'```\s*', '', sql)
    return sql.strip()

async def run_natural_language_query(
    question: str,
    db: AsyncSession
) -> dict:
    if not question or len(question.strip()) < 3:
        return {
            "success": False,
            "error": "Question is too short",
            "results": [],
            "sql": None
        }

    if len(question) > 500:
        return {
            "success": False,
            "error": "Question is too long, keep it under 500 characters",
            "results": [],
            "sql": None
        }

    try:
        sql = generate_sql(question)

        if sql == "INVALID_QUERY":
            return {
                "success": False,
                "error": "Could not generate a valid query for that question",
                "results": [],
                "sql": None
            }

        if not is_safe_query(sql):
            return {
                "success": False,
                "error": "Generated query failed safety validation",
                "results": [],
                "sql": None
            }

        result = await db.execute(text(sql))
        rows = result.fetchall()

        results = []
        for row in rows:
            row_dict = dict(row._mapping)
            for key, value in row_dict.items():
                if hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool, type(None))):
                    row_dict[key] = str(value)
            results.append(row_dict)

        return {
            "success": True,
            "error": None,
            "results": results,
            "sql": sql,
            "count": len(results)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Query execution failed: {str(e)}",
            "results": [],
            "sql": None
        }
    

