from collections import defaultdict

from backend.analytics import GraphAnalytics


class PatternDetector:
    """
    Produces investigator-facing leads from the relationship graph.

    Findings describe observable patterns in supplied records; they are not
    assertions of criminal activity and must be reviewed by an investigator.
    """

    COMMUNICATION_TYPES = {"CALLED", "COMMUNICATED_WITH", "COMMUNICATED"}
    FINANCIAL_TYPES = {
        "TRANSFERRED",
        "TRANSFERRED_TO",
        "TRANSFER",
        "PAID_TO",
        "SENT_TO",
    }

    def __init__(self, graph, records):
        self.graph = graph
        self.records = records or []
        self.analytics = GraphAnalytics(graph)

    def detect_high_connectivity(self, threshold=0.15):
        """Find entities with an unusually high number of direct links."""
        degree_scores = self.analytics.degree_centrality()
        findings = []

        for node, score in degree_scores.items():
            if score < threshold:
                continue

            findings.append({
                "type": "HIGH_CONNECTIVITY",
                "entity": node,
                "entity_type": self.graph.nodes[node].get("type", "UNKNOWN"),
                "score": round(score, 3),
                "connections": self.graph.degree(node),
                "description": (
                    f"{node} has {self.graph.degree(node)} direct network "
                    "connections and should be prioritised for review."
                ),
            })

        return self._sort_findings(findings, "score")

    def detect_network_bridges(self, threshold=0.05):
        """Find entities that connect otherwise separate parts of the graph."""
        betweenness_scores = self.analytics.betweenness_centrality()
        findings = []

        for node, score in betweenness_scores.items():
            if score < threshold:
                continue

            findings.append({
                "type": "NETWORK_BRIDGE",
                "entity": node,
                "entity_type": self.graph.nodes[node].get("type", "UNKNOWN"),
                "score": round(score, 3),
                "description": (
                    f"{node} is a potential bridge between separate parts "
                    "of the analyzed network."
                ),
            })

        return self._sort_findings(findings, "score")

    def detect_high_call_activity(self, threshold=10):
        """
        Aggregate call activity for each pair across all records.
        Aggregating avoids missing a high-volume pair split across CDR files.
        """
        activity = defaultdict(lambda: {
            "count": 0,
            "record_ids": set(),
            "evidence": [],
        })

        for record in self.records:
            for relationship in record.get("relationships", []):
                if relationship.get("relationship", "").upper() not in self.COMMUNICATION_TYPES:
                    continue

                source = relationship.get("source")
                target = relationship.get("target")
                if not source or not target:
                    continue

                count = self._number(
                    relationship.get("count", relationship.get("call_count", 0))
                )
                if count <= 0:
                    continue

                key = self._pair_key(source, target, directional=False)
                activity[key]["count"] += count
                activity[key]["record_ids"].add(record.get("record_id", "UNKNOWN"))
                activity[key]["evidence"].append(relationship.get("evidence", ""))

        findings = []
        for (source, target), data in activity.items():
            if data["count"] < threshold:
                continue

            findings.append({
                "type": "HIGH_CALL_ACTIVITY",
                "source": source,
                "target": target,
                "count": data["count"],
                "record_ids": sorted(data["record_ids"]),
                "description": (
                    f"{source} and {target} have {data['count']} recorded "
                    "communications across the available data."
                ),
            })

        return self._sort_findings(findings, "count")

    def detect_large_transactions(self, threshold=50000):
        """Aggregate transfers between the same directed pair."""
        transactions = defaultdict(lambda: {
            "amount": 0.0,
            "record_ids": set(),
        })

        for record in self.records:
            for relationship in record.get("relationships", []):
                if relationship.get("relationship", "").upper() not in self.FINANCIAL_TYPES:
                    continue

                source = relationship.get("source")
                target = relationship.get("target")
                if not source or not target:
                    continue

                amount = self._number(relationship.get("amount", 0))
                if amount <= 0:
                    continue

                key = self._pair_key(source, target, directional=True)
                transactions[key]["amount"] += amount
                transactions[key]["record_ids"].add(record.get("record_id", "UNKNOWN"))

        findings = []
        for (source, target), data in transactions.items():
            if data["amount"] < threshold:
                continue

            amount = self._clean_number(data["amount"])
            findings.append({
                "type": "LARGE_TRANSACTION",
                "source": source,
                "target": target,
                "amount": amount,
                "record_ids": sorted(data["record_ids"]),
                "description": (
                    f"{source} transferred a total of ₹{amount:,.0f} to "
                    f"{target} in the available records."
                ),
            })

        return self._sort_findings(findings, "amount")

    def detect_shared_locations(self, minimum_people=2):
        """
        Flag locations linked to multiple people. This is an investigative lead,
        not proof that a meeting occurred.
        """
        location_people = defaultdict(set)
        location_records = defaultdict(set)

        for record in self.records:
            for relationship in record.get("relationships", []):
                if relationship.get("relationship") not in {
                    "LOCATED_AT", "ASSOCIATED_WITH", "MET"
                }:
                    continue

                source = relationship.get("source")
                target = relationship.get("target")
                if not source or not target:
                    continue

                source_type = self.graph.nodes.get(source, {}).get("type")
                target_type = self.graph.nodes.get(target, {}).get("type")

                if target_type == "LOCATION":
                    location, person = target, source
                elif source_type == "LOCATION":
                    location, person = source, target
                else:
                    continue

                location_people[location].add(person)
                location_records[location].add(record.get("record_id", "UNKNOWN"))

        findings = []
        for location, people in location_people.items():
            if len(people) < minimum_people:
                continue

            findings.append({
                "type": "SHARED_LOCATION",
                "entity": location,
                "people": sorted(people),
                "person_count": len(people),
                "record_ids": sorted(location_records[location]),
                "description": (
                    f"{len(people)} people are linked to {location} in the "
                    "available evidence and may warrant timeline review."
                ),
            })

        return self._sort_findings(findings, "person_count")

    def detect_communication_financial_overlap(self):
        """Find pairs that appear in both communication and money-transfer data."""
        communication_pairs = set()
        financial_pairs = set()
        records_by_pair = defaultdict(set)

        for record in self.records:
            for relationship in record.get("relationships", []):
                source = relationship.get("source")
                target = relationship.get("target")
                if not source or not target:
                    continue

                pair = self._pair_key(source, target, directional=False)
                relationship_type = relationship.get("relationship", "").upper()
                if relationship_type in self.COMMUNICATION_TYPES:
                    communication_pairs.add(pair)
                    records_by_pair[pair].add(record.get("record_id", "UNKNOWN"))
                elif relationship_type in self.FINANCIAL_TYPES:
                    financial_pairs.add(pair)
                    records_by_pair[pair].add(record.get("record_id", "UNKNOWN"))

        overlap = communication_pairs & financial_pairs
        return [{
            "type": "COMMUNICATION_FINANCIAL_OVERLAP",
            "source": source,
            "target": target,
            "record_ids": sorted(records_by_pair[(source, target)]),
            "description": (
                f"{source} and {target} are linked by both communication and "
                "financial relationships in the available data."
            ),
        } for source, target in sorted(overlap)]

    def calculate_entity_risk_scores(self):
        """
        Rank entities by transparent, evidence-based signals. The score is a
        prioritisation aid only and deliberately does not make a guilt claim.
        """
        degree = self.analytics.degree_centrality()
        betweenness = self.analytics.betweenness_centrality()
        call_findings = self.detect_high_call_activity()
        transfer_findings = self.detect_large_transactions()

        call_score = defaultdict(int)
        transfer_score = defaultdict(int)
        for item in call_findings:
            call_score[item["source"]] += 1
            call_score[item["target"]] += 1
        for item in transfer_findings:
            transfer_score[item["source"]] += 1
            transfer_score[item["target"]] += 1

        findings = []
        for entity in self.graph.nodes:
            score = (
                degree.get(entity, 0) * 40
                + betweenness.get(entity, 0) * 35
                + call_score[entity] * 15
                + transfer_score[entity] * 10
            )
            if score <= 0:
                continue

            findings.append({
                "type": "ENTITY_RISK_INDICATOR",
                "entity": entity,
                "entity_type": self.graph.nodes[entity].get("type", "UNKNOWN"),
                "score": round(min(score, 100), 1),
                "description": (
                    f"{entity} has a prioritisation score of "
                    f"{min(score, 100):.1f}, based on network centrality and "
                    "observed communication or transfer signals."
                ),
            })

        return self._sort_findings(findings, "score")

    def get_patterns(self):
        """
        Keep the original four keys for the current React UI, and expose
        additional evidence-driven pattern categories for an enhanced view.
        """
        return {
            "high_connectivity": self.detect_high_connectivity(),
            "network_bridges": self.detect_network_bridges(),
            "high_call_activity": self.detect_high_call_activity(),
            "large_transactions": self.detect_large_transactions(),
            "shared_locations": self.detect_shared_locations(),
            "communication_financial_overlap": (
                self.detect_communication_financial_overlap()
            ),
            "entity_risk_indicators": self.calculate_entity_risk_scores(),
        }

    @staticmethod
    def _pair_key(source, target, directional):
        source = str(source).strip()
        target = str(target).strip()
        if directional:
            return source, target
        return tuple(sorted((source, target), key=str.lower))

    @staticmethod
    def _number(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _clean_number(value):
        return int(value) if float(value).is_integer() else round(value, 2)

    @staticmethod
    def _sort_findings(findings, field):
        return sorted(findings, key=lambda item: item.get(field, 0), reverse=True)