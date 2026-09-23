from collections import Counter, defaultdict

from backend.analytics import GraphAnalytics
from backend.correlation_engine import CorrelationEngine
from backend.evidence_tracker import EvidenceTracker
from backend.pattern_detector import PatternDetector


class InvestigationEngine:
    """
    Coordinates graph analytics, pattern detection, evidence tracing, and
    cross-source correlation for investigator decision support.

    Outputs are investigative leads based only on supplied data. They must be
    reviewed and corroborated by an authorized human investigator.
    """

    def __init__(self, records, graph):
        self.records = records or []
        self.graph = graph
        self.analytics = GraphAnalytics(graph)
        self.pattern_detector = PatternDetector(graph, self.records)
        self.correlation_engine = CorrelationEngine(self.records)
        self.evidence_tracker = EvidenceTracker(self.records)

    def get_network_summary(self):
        """Return network size, composition, and available-source coverage."""
        entity_types = Counter(
            data.get("type", "UNKNOWN")
            for _, data in self.graph.nodes(data=True)
        )
        relationship_types = Counter(
            data.get("relationship", "UNKNOWN")
            for _, _, data in self.graph.edges(data=True)
        )
        source_types = Counter(
            record.get("record_type", "UNKNOWN")
            for record in self.records
        )

        return {
            "total_entities": self.graph.number_of_nodes(),
            "total_relationships": self.graph.number_of_edges(),
            "total_records": len(self.records),
            "entity_types": dict(sorted(entity_types.items())),
            "relationship_types": dict(sorted(relationship_types.items())),
            "source_types": dict(sorted(source_types.items())),
        }

    def get_key_entities(self, limit=None):
        """
        Rank entities using network centrality plus explicit pattern signals.
        The score is transparent and meant to guide review order, not infer
        culpability.
        """
        degree_scores = self.analytics.degree_centrality()
        betweenness_scores = self.analytics.betweenness_centrality()
        risk_indicators = {
            item["entity"]: item["score"]
            for item in self._risk_indicators()
        }

        entities = []
        for node, data in self.graph.nodes(data=True):
            degree = degree_scores.get(node, 0)
            betweenness = betweenness_scores.get(node, 0)
            pattern_score = risk_indicators.get(node, 0)

            # Centrality carries most of the score; the detector adds only
            # observed communication/financial signals.
            priority_score = min(
                100,
                (degree * 45 + betweenness * 35 + pattern_score * 0.20),
            )

            entities.append({
                "entity": node,
                "type": data.get("type", "UNKNOWN"),
                "degree_centrality": round(degree, 3),
                "betweenness_centrality": round(betweenness, 3),
                "priority_score": round(priority_score, 1),
                "evidence_records": len(
                    self.evidence_tracker.get_entity_evidence(node)
                ),
            })

        entities.sort(
            key=lambda item: (
                item["priority_score"],
                item["degree_centrality"],
                item["betweenness_centrality"],
            ),
            reverse=True,
        )
        return entities[:limit] if limit is not None else entities

    def get_patterns(self):
        """
        Use the expanded detector when available. The fallback preserves
        compatibility with the original PatternDetector.
        """
        if hasattr(self.pattern_detector, "get_patterns"):
            return self.pattern_detector.get_patterns()

        return {
            "high_connectivity": self.pattern_detector.detect_high_connectivity(),
            "network_bridges": self.pattern_detector.detect_network_bridges(),
            "high_call_activity": self.pattern_detector.detect_high_call_activity(),
            "large_transactions": self.pattern_detector.detect_large_transactions(),
        }

    def get_correlations(self):
        return {
            "communication_financial": (
                self.correlation_engine.detect_communication_financial_links()
            ),
            "multi_source_entities": (
                self.correlation_engine.detect_multi_source_entities()
            ),
        }

    def generate_investigation_brief(self, entity_limit=5, lead_limit=10):
        """
        Return a compact, API-friendly brief for a dashboard or case file.
        """
        summary = self.get_network_summary()
        key_entities = self.get_key_entities(limit=entity_limit)
        patterns = self.get_patterns()
        correlations = self.get_correlations()
        leads = self._prioritised_leads(patterns, correlations, lead_limit)

        return {
            "network_summary": summary,
            "priority_entities": key_entities,
            "patterns": patterns,
            "correlations": correlations,
            "priority_leads": leads,
            "analyst_note": (
                "Results identify patterns in the supplied information. "
                "They are investigative leads and require human review and "
                "independent corroboration."
            ),
        }

    def generate_summary(self):
        """Print and return the full investigator-facing intelligence brief."""
        brief = self.generate_investigation_brief()
        summary = brief["network_summary"]

        print("\n" + "=" * 70)
        print("UNIFIED INVESTIGATION ANALYSIS")
        print("=" * 70)
        print(
            f"Records: {summary['total_records']} | "
            f"Entities: {summary['total_entities']} | "
            f"Relationships: {summary['total_relationships']}"
        )

        print("\nPRIORITY ENTITIES")
        print("-" * 45)
        for entity in brief["priority_entities"]:
            print(
                f"• {entity['entity']} ({entity['type']}) — "
                f"priority score {entity['priority_score']}"
            )

        print("\nPRIORITY LEADS")
        print("-" * 45)
        for lead in brief["priority_leads"]:
            print(f"• {lead['description']}")

        print("\nANALYST NOTE")
        print("-" * 45)
        print(brief["analyst_note"])

        return brief

    def _risk_indicators(self):
        detector = self.pattern_detector
        if not hasattr(detector, "calculate_entity_risk_scores"):
            return []
        return detector.calculate_entity_risk_scores()

    @staticmethod
    def _prioritised_leads(patterns, correlations, limit):
        """
        Deduplicate findings into a readable ordered lead list. Scores are
        ordering aids only; factual descriptions remain in each lead.
        """
        category_weight = {
            "entity_risk_indicators": 5,
            "communication_financial_overlap": 4,
            "large_transactions": 4,
            "high_call_activity": 3,
            "network_bridges": 3,
            "shared_locations": 2,
            "high_connectivity": 2,
        }
        leads = []
        seen = set()

        for category, findings in patterns.items():
            for finding in findings:
                description = finding.get("description", "")
                if not description or description in seen:
                    continue
                seen.add(description)
                leads.append({
                    **finding,
                    "category": category,
                    "priority": category_weight.get(category, 1),
                })

        for category, findings in correlations.items():
            for finding in findings:
                description = finding.get("description", "")
                if not description or description in seen:
                    continue
                seen.add(description)
                leads.append({
                    **finding,
                    "category": category,
                    "priority": 4,
                })

        leads.sort(
            key=lambda item: (
                item["priority"],
                item.get("score", 0),
                item.get("amount", 0),
                item.get("count", 0),
            ),
            reverse=True,
        )
        return leads[:limit]