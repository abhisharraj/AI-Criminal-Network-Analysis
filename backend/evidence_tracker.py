import os



class EvidenceTracker:

    def __init__(self, records):
        self.records = records

    # -------------------------------------------------
    # Get evidence for a specific entity
    # -------------------------------------------------

    def get_entity_evidence(self, entity_name):

        evidence = []

        for record in self.records:

            for entity in record["entities"]:

                if entity["text"].strip().lower() == entity_name.strip().lower():

                    evidence.append({
                        "record_id": record["record_id"],
                        "record_type": record["record_type"],
                        "source": record["source"],
                        "text": record["text"]
                    })

                    break

        return evidence

    # -------------------------------------------------
    # Get evidence for a relationship
    # -------------------------------------------------

    def get_relationship_evidence(
        self,
        source_entity,
        target_entity,
        relationship_type
    ):

        evidence = []

        for record in self.records:

            for relationship in record["relationships"]:

                if (
                    relationship["source"].strip().lower()
                    == source_entity.strip().lower()
                    and
                    relationship["target"].strip().lower()
                    == target_entity.strip().lower()
                    and
                    relationship["relationship"]
                    == relationship_type
                ):

                    evidence_item = {
                        "record_id": record["record_id"],
                        "record_type": record["record_type"],
                        "source": record["source"],
                        "text": record["text"]
                    }

                    # Add relationship metadata if available

                    call_count = relationship.get(
                        "count",
                        relationship.get("call_count")
                    )

                    if call_count is not None:
                        evidence_item["count"] = call_count

                    if "amount" in relationship:
                        evidence_item["amount"] = relationship["amount"]

                    evidence.append(evidence_item)

        return evidence

    # -------------------------------------------------
    # Display entity evidence
    # -------------------------------------------------

    def display_entity_evidence(self, entity_name):

        print("\n")
        print("=" * 60)
        print("ENTITY EVIDENCE")
        print("=" * 60)

        print(f"\nEntity: {entity_name}")

        evidence = self.get_entity_evidence(
            entity_name
        )

        if not evidence:

            print("\nNo evidence found.")

            return

        print(
            f"\nFound in {len(evidence)} record(s):"
        )

        for item in evidence:

            print("\n----------------------------------------")

            print(
                f"Record ID: {item['record_id']}"
            )

            print(
                f"Record Type: {item['record_type']}"
            )

            print(
                f"Source: {item['source']}"
            )

            print(
                f"Original Text: {item['text']}"
            )

    # -------------------------------------------------
    # Display relationship evidence
    # -------------------------------------------------

    def display_relationship_evidence(
        self,
        source_entity,
        target_entity,
        relationship_type
    ):

        print("\n")
        print("=" * 60)
        print("RELATIONSHIP EVIDENCE")
        print("=" * 60)

        print(
            f"\nRelationship: "
            f"{source_entity} "
            f"--{relationship_type}--> "
            f"{target_entity}"
        )

        evidence = self.get_relationship_evidence(
            source_entity,
            target_entity,
            relationship_type
        )

        if not evidence:

            print("\nNo evidence found.")

            return

        print(
            f"\nFound in {len(evidence)} record(s):"
        )

        for item in evidence:

            print("\n----------------------------------------")

            print(
                f"Record ID: {item['record_id']}"
            )

            print(
                f"Record Type: {item['record_type']}"
            )

            print(
                f"Source: {item['source']}"
            )

            if "count" in item:

                print(
                    f"Call Count: {item['count']}"
                )

            if "amount" in item:

                print(
                    f"Amount: ₹{item['amount']:,}"
                )

            print(
                f"Original Text: {item['text']}"
            )


# -------------------------------------------------
# MAIN
# -------------------------------------------------

if __name__ == "__main__":

    backend_folder = os.path.dirname(
        os.path.abspath(__file__)
    )

    project_folder = os.path.dirname(
        backend_folder
    )

    data_file = os.path.join(
        project_folder,
        "data",
        "sample_data.csv"
    )

    print("Using dataset:")
    print(data_file)

    # Process dataset

    processor = DataProcessor(
        data_file
    )

    records = processor.process_data()

    # Create evidence tracker

    tracker = EvidenceTracker(
        records
    )

    # ---------------------------------------------
    # Test entity evidence
    # ---------------------------------------------

    tracker.display_entity_evidence(
        "Rahul Sharma"
    )

    # ---------------------------------------------
    # Test relationship evidence
    # ---------------------------------------------

    tracker.display_relationship_evidence(
        "Rahul Sharma",
        "Amit Verma",
        "CALLED"
    )