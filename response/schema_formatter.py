from typing import Dict, List


def format_schema(schema_context: dict) -> str:
    lines = ["## Relevant Table Schema\n"]
    for table in schema_context.get("tables", []):
        if table.get("description"):
            lines.append(f"-- {table['name']}: {table['description']}")
        lines.append(table["ddl"])
        rows = table.get("sample_rows", [])
        if rows:
            lines.append(f"-- Sample data ({table['name']}):")
            lines.append("-- " + " | ".join(table["columns"]))
            for row in rows:
                lines.append("-- " + " | ".join(str(v) for v in row.values()))
        lines.append("")
    join_paths = schema_context.get("join_paths", [])
    if join_paths:
        lines.append("## Table Relationships (JOIN Conditions)")
        for jp in join_paths:
            lines.append(f"- {jp}")
    return "\n".join(lines)


def format_roles(roles: dict) -> str:
    entity_names = [
        e.get("normalized", e.get("original", ""))
        for e in roles.get("entity", [])
        if isinstance(e, dict)
    ]
    location_names = [
        e.get("normalized", e.get("original", ""))
        for e in roles.get("location", [])
        if isinstance(e, dict)
    ]
    lines = []
    if roles.get("metric"):      lines.append(f"- Metric: {', '.join(roles['metric'])}")
    if roles.get("time"):        lines.append(f"- Time: {', '.join(roles['time'])}")
    if roles.get("comparison"):  lines.append(f"- Comparison/Ranking: {', '.join(roles['comparison'])}")
    if roles.get("status"):      lines.append(f"- Status Filter: {', '.join(roles['status'])}")
    if roles.get("aggregation"): lines.append(f"- Grouping Dimension: {', '.join(roles['aggregation'])}")
    if roles.get("limit"):       lines.append(f"- Limit: {', '.join(roles['limit'])}")
    if entity_names:             lines.append(f"- Entity Filter: {', '.join(entity_names)}")
    if location_names:           lines.append(f"- Location Filter: {', '.join(location_names)}")
    return "\n".join(lines) if lines else ""
