import os
import re
from collections import defaultdict

from rapidfuzz import fuzz


class EntityResolver:
    """
    Finds possible references to the same real-world entity across case data.

    It never treats a fuzzy name match as a confirmed identity. Results include
    a confidence level and are intended for investigator review.
    """

    SUPPORTED_TYPES = {
        "PERSON",
        "LOCATION",
        "VEHICLE",
        "PHONE",
        "ORGANIZATION",
        "ORG",
    }
    IDENTIFIER_TYPES = {"PHONE", "VEHICLE"}

    def __init__(
        self,
        records,
        similarity_threshold=85,
        auto_merge_threshold=96,
    ):
        self.records = records or []
        self.similarity_threshold = similarity_threshold
        self.auto_merge_threshold = auto_merge_threshold

    def collect_entities(self):
        """
        Collect entities with source-record provenance. Exact normalized values
        are already merged here; fuzzy candidates are handled separately.
        """
        entities = {}

        for record in self.records:
            for entity in record.get("entities", []):
                name = str(entity.get("text", "")).strip()
                entity_type = self._entity_type(entity.get("label"))
                if not name or entity_type not in self.SUPPORTED_TYPES:
                    continue

                normalized = self.normalize_name(name, entity_type)
                if not normalized:
                    continue

                key = (entity_type, normalized)
                if key not in entities:
                    entities[key] = {
                        "name": name,
                        "normalized_name": normalized,
                        "type": entity_type,
                        "records": set(),
                        "sources": set(),
                        "aliases": set(),
                    }

                item = entities[key]
                item["records"].add(record.get("record_id", "UNKNOWN"))
                item["sources"].add(record.get("source", "UNKNOWN"))
                item["aliases"].add(name)

                # Prefer the longest alias as the display name because it is
                # usually less abbreviated (for example, Rahul K Sharma).
                if len(name) > len(item["name"]):
                    item["name"] = name

        return entities

    def normalize_name(self, name, entity_type):
        """Normalize formatting without discarding identity-significant text."""
        value = str(name).strip().lower()

        if entity_type in self.IDENTIFIER_TYPES:
            return re.sub(r"[^a-z0-9]", "", value)

        value = re.sub(r"[^a-z0-9\s]", " ", value)
        return re.sub(r"\s+", " ", value).strip()

    def calculate_similarity(self, name1, name2, entity_type="PERSON"):
        """
        Calculate a type-aware candidate score.

        Phones and vehicles must match exactly. People require the same surname
        and compatible first initial before a fuzzy score can be returned.
        """
        normalized_1 = self.normalize_name(name1, entity_type)
        normalized_2 = self.normalize_name(name2, entity_type)

        if not normalized_1 or not normalized_2:
            return 0.0
        if normalized_1 == normalized_2:
            return 100.0
        if entity_type in self.IDENTIFIER_TYPES:
            return 0.0
        if entity_type == "PERSON" and not self._compatible_person_names(
            normalized_1, normalized_2
        ):
            return 0.0

        return round(
            max(
                fuzz.token_set_ratio(normalized_1, normalized_2),
                fuzz.ratio(normalized_1, normalized_2),
            ),
            2,
        )

    def find_possible_matches(self):
        """
        Return candidate aliases with review status and record provenance.
        Identifier types only produce exact-normalization matches.
        """
        entities = list(self.collect_entities().values())
        matches = []

        for index, entity_1 in enumerate(entities):
            for entity_2 in entities[index + 1:]:
                if entity_1["type"] != entity_2["type"]:
                    continue

                entity_type = entity_1["type"]
                score = self.calculate_similarity(
                    entity_1["name"],
                    entity_2["name"],
                    entity_type,
                )
                if score < self.similarity_threshold:
                    continue

                confidence = self._confidence(score, entity_type)
                matches.append({
                    "entity_1": entity_1["name"],
                    "entity_2": entity_2["name"],
                    "type": entity_type,
                    "similarity": score,
                    "confidence": confidence,
                    "resolution_status": "REVIEW_REQUIRED",
                    "suggested_canonical_name": self._canonical_name(
                        entity_1["name"], entity_2["name"]
                    ),
                    "records_1": sorted(entity_1["records"]),
                    "records_2": sorted(entity_2["records"]),
                    "sources_1": sorted(entity_1["sources"]),
                    "sources_2": sorted(entity_2["sources"]),
                })

        return sorted(
            matches,
            key=lambda item: (
                self._confidence_rank(item["confidence"]),
                item["similarity"],
            ),
            reverse=True,
        )

    def get_entity_registry(self):
        """Return deduplicated exact entities with aliases and provenance."""
        registry = []
        for entity in self.collect_entities().values():
            registry.append({
                "name": entity["name"],
                "type": entity["type"],
                "aliases": sorted(entity["aliases"]),
                "record_ids": sorted(entity["records"]),
                "sources": sorted(entity["sources"]),
            })

        return sorted(
            registry,
            key=lambda item: (item["type"], item["name"].lower()),
        )

    def resolution_report(self):
        """Return API-friendly entity-resolution results."""
        candidates = self.find_possible_matches()
        return {
            "entity_registry": self.get_entity_registry(),
            "possible_matches": candidates,
            "summary": {
                "unique_entities": len(self.collect_entities()),
                "possible_matches": len(candidates),
                "high_confidence_matches": sum(
                    item["confidence"] == "HIGH" for item in candidates
                ),
                "review_required": True,
            },
            "analyst_note": (
                "Entity-resolution candidates are based on supplied data and "
                "must be verified by an investigator before records are merged."
            ),
        }

    @staticmethod
    def _entity_type(entity_type):
        normalized = str(entity_type or "UNKNOWN").upper()
        return "ORGANIZATION" if normalized == "ORG" else normalized

    @staticmethod
    def _compatible_person_names(name_1, name_2):
        tokens_1 = name_1.split()
        tokens_2 = name_2.split()
        if len(tokens_1) < 2 or len(tokens_2) < 2:
            return False

        # A shared surname plus compatible first-name initial is a minimum
        # safety check before considering a fuzzy person-name match.
        return (
            tokens_1[-1] == tokens_2[-1]
            and tokens_1[0][0] == tokens_2[0][0]
        )

    @staticmethod
    def _canonical_name(name_1, name_2):
        return max((name_1, name_2), key=lambda value: (len(value), value))

    def _confidence(self, score, entity_type):
        if entity_type in self.IDENTIFIER_TYPES:
            return "HIGH" if score == 100 else "LOW"
        if score >= self.auto_merge_threshold:
            return "HIGH"
        if score >= 90:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _confidence_rank(confidence):
        return {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(confidence, 0)

    def display_matches(self):
        """Print candidates for local testing without treating them as merges."""
        report = self.resolution_report()
        print("\n" + "=" * 60)
        print("ENTITY RESOLUTION ANALYSIS")
        print("=" * 60)

        matches = report["possible_matches"]
        if not matches:
            print("\nNo possible matches found.")
            return

        for match in matches:
            print(
                f"\n{match['entity_1']} <--> {match['entity_2']} "
                f"({match['type']}, {match['similarity']}%)"
            )
            print(f"  Confidence: {match['confidence']}")
            print(f"  Suggested canonical name: {match['suggested_canonical_name']}")
            print("  Status: REVIEW REQUIRED")


if __name__ == "__main__":
    from backend.data_processor import DataProcessor

    backend_folder = os.path.dirname(os.path.abspath(__file__))
    project_folder = os.path.dirname(backend_folder)
    data_file = os.path.join(project_folder, "data", "sample_data.csv")

    records = DataProcessor(data_file).process_data()
    EntityResolver(records).display_matches()