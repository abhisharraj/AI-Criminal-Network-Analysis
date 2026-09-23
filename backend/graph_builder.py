import os

import networkx as nx


class GraphBuilder:
    """
    Build a provenance-aware criminal-network graph.

    A MultiDiGraph keeps relationship direction and different relationship
    types, while repeated evidence for the same source/target/type is merged
    into one edge. This keeps the visual map readable and preserves totals.
    """

    EXCLUDED_NODE_TYPES = {"DATE", "AMOUNT", "CALL_COUNT"}

    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def add_entities(self, entities):
        """Add supported extracted entities as typed graph nodes."""
        for entity in entities or []:
            name = str(entity.get("text", "")).strip()
            entity_type = str(entity.get("label", "UNKNOWN")).upper()
            if not name or entity_type in self.EXCLUDED_NODE_TYPES:
                continue

            existing = self.graph.nodes.get(name, {})
            node_type = (
                existing.get("type")
                if existing.get("type") and existing.get("type") != "UNKNOWN"
                else entity_type
            )
            self.graph.add_node(
                name,
                type=node_type,
                sources=self._append_unique(
                    existing.get("sources", []),
                    entity.get("source"),
                ),
            )

    def add_relationships(self, relationships, record_id=None):
        """
        Add relationships and merge duplicate relationship types.

        Communication counts and financial amounts are summed. Evidence and
        record IDs remain available for traceability in the API and UI.
        """
        for relationship in relationships or []:
            source = str(relationship.get("source", "")).strip()
            target = str(relationship.get("target", "")).strip()
            relationship_type = str(
                relationship.get("relationship", "UNKNOWN")
            ).upper()

            if not source or not target or source == target:
                continue

            self._ensure_relationship_node(source)
            self._ensure_relationship_node(target)

            edge_key = relationship_type
            previous = self.graph.get_edge_data(source, target, edge_key, {})

            count = self._number(
                relationship.get("count", relationship.get("call_count", 0))
            )
            amount = self._number(relationship.get("amount", 0))

            edge_data = {
                "relationship": relationship_type,
                "count": self._clean_number(
                    self._number(previous.get("count", 0)) + count
                ),
                "amount": self._clean_number(
                    self._number(previous.get("amount", 0)) + amount
                ),
                "evidence": self._append_unique(
                    previous.get("evidence", []),
                    relationship.get("evidence"),
                ),
                "record_ids": self._append_unique(
                    previous.get("record_ids", []),
                    record_id,
                ),
            }

            if not edge_data["count"]:
                edge_data.pop("count")
            if not edge_data["amount"]:
                edge_data.pop("amount")

            self.graph.add_edge(source, target, key=edge_key, **edge_data)

    def build(self, records):
        """Build a fresh graph from normalized investigation records."""
        self.graph = nx.MultiDiGraph()

        for record in records or []:
            self.add_entities(record.get("entities", []))
            self.add_relationships(
                record.get("relationships", []),
                record.get("record_id"),
            )

        return self.graph

    def get_summary(self):
        """Return graph composition useful for the dashboard/API."""
        entity_types = {}
        relationship_types = {}

        for _, data in self.graph.nodes(data=True):
            node_type = data.get("type", "UNKNOWN")
            entity_types[node_type] = entity_types.get(node_type, 0) + 1

        for _, _, data in self.graph.edges(data=True):
            relationship_type = data.get("relationship", "UNKNOWN")
            relationship_types[relationship_type] = (
                relationship_types.get(relationship_type, 0) + 1
            )

        return {
            "total_entities": self.graph.number_of_nodes(),
            "total_relationships": self.graph.number_of_edges(),
            "entity_types": dict(sorted(entity_types.items())),
            "relationship_types": dict(sorted(relationship_types.items())),
        }

    def display_graph(self):
        """Print a concise, provenance-aware graph report for local testing."""
        summary = self.get_summary()
        print("\n" + "=" * 40)
        print("CRIMINAL NETWORK GRAPH")
        print("=" * 40)
        print(f"Entities: {summary['total_entities']}")
        print(f"Relationships: {summary['total_relationships']}")

        print("\nNODES")
        for node, data in self.graph.nodes(data=True):
            print(f"  {node} -> {data.get('type', 'UNKNOWN')}")

        print("\nRELATIONSHIPS")
        for source, target, data in self.graph.edges(data=True):
            details = []
            if "count" in data:
                details.append(f"calls: {data['count']}")
            if "amount" in data:
                details.append(f"amount: ₹{data['amount']:,.0f}")
            if data.get("record_ids"):
                details.append(f"records: {', '.join(data['record_ids'])}")
            suffix = f" ({'; '.join(details)})" if details else ""
            print(
                f"  {source} --{data.get('relationship', 'UNKNOWN')}--> "
                f"{target}{suffix}"
            )

    def _ensure_relationship_node(self, name):
        """Create an untyped node for a relationship-only entity if required."""
        if name not in self.graph:
            self.graph.add_node(name, type="UNKNOWN", sources=[])

    @staticmethod
    def _append_unique(items, value):
        values = list(items or [])
        if value is not None and value != "" and value not in values:
            values.append(value)
        return values

    @staticmethod
    def _number(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _clean_number(value):
        return int(value) if float(value).is_integer() else round(value, 2)


if __name__ == "__main__":
    from backend.data_processor import DataProcessor

    backend_folder = os.path.dirname(os.path.abspath(__file__))
    project_folder = os.path.dirname(backend_folder)
    data_file = os.path.join(project_folder, "data", "sample_data.csv")

    records = DataProcessor(data_file).process_data()
    builder = GraphBuilder()
    builder.build(records)
    builder.display_graph()