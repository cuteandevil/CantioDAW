from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import yaml
from pathlib import Path


@dataclass
class ParameterEffect:
    target: str
    delta: float


@dataclass
class GraphNode:
    id: str
    label: str
    affects: List[ParameterEffect] = field(default_factory=list)
    inverse: List[ParameterEffect] = field(default_factory=list)
    related: List[str] = field(default_factory=list)


class KnowledgeGraph:
    def __init__(self, nodes: Optional[Dict[str, GraphNode]] = None):
        self.nodes: Dict[str, GraphNode] = nodes or {}

    @classmethod
    def load(cls, path: str | Path) -> KnowledgeGraph:
        path = Path(path)
        if not path.exists():
            return cls()
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        nodes = {}
        for node_data in data.get("nodes", []):
            n = GraphNode(
                id=node_data["id"],
                label=node_data.get("label", node_data["id"]),
                affects=[ParameterEffect(**a) for a in node_data.get("affects", [])],
                inverse=[ParameterEffect(**a) for a in node_data.get("inverse", [])],
                related=node_data.get("related", []),
            )
            nodes[n.id] = n
        return cls(nodes)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        data = {"nodes": []}
        for node in self.nodes.values():
            data["nodes"].append({
                "id": node.id,
                "label": node.label,
                "affects": [{"target": a.target, "delta": a.delta} for a in node.affects],
                "inverse": [{"target": a.target, "delta": a.delta} for a in node.inverse],
                "related": node.related,
            })
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    def query(self, concept: str, direction: Optional[str] = None) -> List[ParameterEffect]:
        node = self.nodes.get(concept)
        if not node:
            return []
        if direction == "inverse":
            return node.inverse
        return node.affects

    def reverse_query(self, target_param: str) -> List[str]:
        results = []
        for nid, node in self.nodes.items():
            for effect in node.affects:
                if effect.target == target_param:
                    results.append(nid)
        return results

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node

    def get_node(self, concept: str) -> Optional[GraphNode]:
        return self.nodes.get(concept)

    def list_concepts(self) -> List[str]:
        return list(self.nodes.keys())
