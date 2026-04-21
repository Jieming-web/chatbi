from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TableInfo:
    name: str
    description: str
    ddl: str
    columns: List[str]
    sample_rows: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "ddl": self.ddl,
            "columns": self.columns,
            "sample_rows": self.sample_rows,
        }


@dataclass
class SchemaContext:
    tables: List[TableInfo] = field(default_factory=list)
    join_paths: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tables": [t.to_dict() for t in self.tables],
            "join_paths": list(self.join_paths),
        }


@dataclass
class EntityCandidate:
    original: str
    normalized: str
    group: str


@dataclass
class Roles:
    metric: List[str] = field(default_factory=list)
    time: List[str] = field(default_factory=list)
    comparison: List[str] = field(default_factory=list)
    status: List[str] = field(default_factory=list)
    aggregation: List[str] = field(default_factory=list)
    limit: List[str] = field(default_factory=list)
    entity: List[EntityCandidate] = field(default_factory=list)
    location: List[EntityCandidate] = field(default_factory=list)
