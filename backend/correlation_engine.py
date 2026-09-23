from collections import defaultdict


class CorrelationEngine:

    def __init__(self, records):

        self.records = records or []

    # =========================================================
    # 1. COMMUNICATION + FINANCIAL CORRELATION
    # =========================================================

    def detect_communication_financial_links(self):

        correlations = []

        communication = defaultdict(list)
        financial = defaultdict(list)

        # -----------------------------------------------------
        # Collect communication and financial relationships
        # -----------------------------------------------------

        for record in self.records:

            record_id = record.get(
                "record_id",
                "UNKNOWN"
            )

            source = record.get(
                "source",
                "UNKNOWN"
            )

            record_type = record.get(
                "record_type",
                "UNKNOWN"
            )

            for relationship in record.get(
                "relationships",
                []
            ):

                rel_type = relationship.get(
                    "relationship",
                    ""
                ).upper()

                source_entity = relationship.get(
                    "source"
                )

                target_entity = relationship.get(
                    "target"
                )

                if not source_entity or not target_entity:
                    continue

                # -------------------------------------------------
                # Communication
                # -------------------------------------------------

                if rel_type in [
                    "COMMUNICATED_WITH",
                    "CALLED",
                    "COMMUNICATED"
                ]:

                    key = self._relationship_key(
                        source_entity,
                        target_entity
                    )

                    communication[key].append({

                        "source": source_entity,

                        "target": target_entity,

                        "count":
                            relationship.get(
                                "count",
                                relationship.get(
                                    "call_count",
                                    0
                                )
                            ),

                        "record_id": record_id,

                        "source_name": source,

                        "record_type": record_type,

                        "evidence":
                            relationship.get(
                                "evidence",
                                ""
                            )
                    })

                # -------------------------------------------------
                # Financial
                # -------------------------------------------------

                if rel_type in [
                    "TRANSFERRED",
                    "TRANSFERRED_TO",
                    "TRANSFER",
                    "PAID_TO",
                    "SENT_TO"
                ]:

                    key = self._relationship_key(
                        source_entity,
                        target_entity
                    )

                    financial[key].append({

                        "source": source_entity,

                        "target": target_entity,

                        "amount":
                            self._numeric_amount(
                                relationship.get(
                                    "amount",
                                    0
                                )
                            ),

                        "record_id": record_id,

                        "source_name": source,

                        "record_type": record_type,

                        "evidence":
                            relationship.get(
                                "evidence",
                                ""
                            )
                    })

        # -----------------------------------------------------
        # Match communication + financial relationships
        # -----------------------------------------------------

        for key in communication:

            if key not in financial:
                continue

            communication_items = (
                communication[key]
            )

            financial_items = (
                financial[key]
            )

            for comm in communication_items:

                for money in financial_items:

                    call_count = comm.get(
                        "count",
                        0
                    )

                    amount = money.get(
                        "amount",
                        0
                    )

                    correlations.append({

                        "type":
                            "COMMUNICATION_FINANCIAL",

                        "source":
                            comm["source"],

                        "target":
                            comm["target"],

                        "call_count":
                            call_count,

                        "amount":
                            amount,

                        "communication_record":
                            comm["record_id"],

                        "financial_record":
                            money["record_id"],

                        "communication_source":
                            comm["source_name"],

                        "financial_source":
                            money["source_name"],

                        "description":
                            (
                                f"{comm['source']} and "
                                f"{comm['target']} show both "
                                f"communication and financial "
                                f"activity "
                                f"({call_count} calls, "
                                f"₹{amount:,.0f} transfer)."
                            )

                    })

        return correlations

    # =========================================================
    # 2. MULTI-SOURCE ENTITIES
    # =========================================================

    def detect_multi_source_entities(
        self,
        minimum_sources=2
    ):

        entity_sources = defaultdict(
            set
        )

        entity_records = defaultdict(
            list
        )

        # -----------------------------------------------------
        # Collect entity appearances
        # -----------------------------------------------------

        for record in self.records:

            record_id = record.get(
                "record_id",
                "UNKNOWN"
            )

            record_type = record.get(
                "record_type",
                "UNKNOWN"
            )

            source = record.get(
                "source",
                record_type
            )

            source_identifier = (
                source
                if source
                else record_type
            )

            for entity in record.get(
                "entities",
                []
            ):

                entity_name = entity.get(
                    "text"
                )

                if not entity_name:
                    continue

                normalized_name = (
                    entity_name
                    .strip()
                    .lower()
                )

                entity_sources[
                    normalized_name
                ].add(
                    source_identifier
                )

                entity_records[
                    normalized_name
                ].append({

                    "entity":
                        entity_name,

                    "record_id":
                        record_id,

                    "record_type":
                        record_type,

                    "source":
                        source_identifier
                })

        # -----------------------------------------------------
        # Build results
        # -----------------------------------------------------

        correlations = []

        for normalized_name, sources in (
            entity_sources.items()
        ):

            if len(sources) < minimum_sources:
                continue

            appearances = entity_records[
                normalized_name
            ]

            entity_name = appearances[0][
                "entity"
            ]

            correlations.append({

                "type":
                    "MULTI_SOURCE_ENTITY",

                "entity":
                    entity_name,

                "source_count":
                    len(sources),

                "sources":
                    sorted(
                        list(sources)
                    ),

                "record_count":
                    len(appearances),

                "record_ids":
                    sorted(
                        list({
                            item["record_id"]
                            for item in appearances
                        })
                    ),

                "description":
                    (
                        f"{entity_name} appears "
                        f"across {len(sources)} "
                        f"intelligence sources."
                    )

            })

        # Highest source coverage first
        correlations.sort(
            key=lambda x:
                x["source_count"],
            reverse=True
        )

        return correlations

    # =========================================================
    # HELPERS
    # =========================================================

    def _relationship_key(
        self,
        source,
        target
    ):

        return (
            source.strip().lower(),
            target.strip().lower()
        )

    # ---------------------------------------------------------

    def _numeric_amount(
        self,
        amount
    ):

        if amount is None:
            return 0

        if isinstance(
            amount,
            (int, float)
        ):

            return float(amount)

        try:

            cleaned = (
                str(amount)
                .replace(",", "")
                .replace("₹", "")
                .replace("INR", "")
                .replace("Rs.", "")
                .replace("Rs", "")
                .strip()
            )

            return float(
                cleaned
            )

        except (
            ValueError,
            TypeError
        ):

            return 0


# =============================================================
# TEST
# =============================================================

if __name__ == "__main__":

    records = [

        {

            "record_id":
                "FIR001",

            "record_type":
                "FIR",

            "source":
                "fir2.txt",

            "entities": [

                {
                    "text":
                        "Rajesh Singh"
                },

                {
                    "text":
                        "Mohan Yadav"
                }

            ],

            "relationships": [

                {

                    "source":
                        "Rajesh Singh",

                    "target":
                        "Mohan Yadav",

                    "relationship":
                        "COMMUNICATED_WITH",

                    "count":
                        15,

                    "evidence":
                        "Rajesh Singh contacted Mohan Yadav 15 times."

                },

                {

                    "source":
                        "Rajesh Singh",

                    "target":
                        "Mohan Yadav",

                    "relationship":
                        "TRANSFERRED_TO",

                    "amount":
                        75000,

                    "evidence":
                        "Rajesh Singh transferred 75000 INR to Mohan Yadav."

                }

            ]

        }

    ]

    engine = CorrelationEngine(
        records
    )

    print("\nCOMMUNICATION + FINANCIAL")
    print("-" * 40)

    for item in engine.detect_communication_financial_links():

        print(item)

    print("\nMULTI-SOURCE ENTITIES")
    print("-" * 40)

    for item in engine.detect_multi_source_entities():

        print(item)
