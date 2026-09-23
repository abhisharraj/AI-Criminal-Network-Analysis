import re


class RelationshipExtractor:

    def __init__(self):

        # =====================================================
        # Relationship keywords
        # =====================================================

        self.relationship_keywords = {

            "COMMUNICATED_WITH": [
                "called",
                "contacted",
                "communicated with",
                "spoke with",
                "talked to",
                "texted",
                "messaged",
                "phoned",
                "telephoned"
            ],

            "MET": [
                "met",
                "meet",
                "meeting",
                "visited",
                "encountered"
            ],

            "TRAVELLED_WITH": [
                "travelled with",
                "traveled with",
                "went with",
                "moved with",
                "accompanied",
                "accompanying"
            ],

            "TRANSFERRED_TO": [
                "transferred to",
                "sent to",
                "paid to",
                "transferred",
                "deposited into",
                "deposited to"
            ],

            "OWNED": [
                "owned",
                "owns",
                "belonged to",
                "registered to",
                "possessed"
            ],

            "USED": [
                "used",
                "using",
                "drove",
                "driving",
                "carried"
            ],

            "ASSOCIATED_WITH": [
                "associated with",
                "linked to",
                "connected to",
                "related to",
                "involved with"
            ]
        }

    # =========================================================
    # MAIN FUNCTION
    # =========================================================

    def extract_relationships(self, text, entities):

        relationships = []

        if not text or not text.strip():
            return relationships

        if not entities:
            return relationships

        # =====================================================
        # Prepare entity lists
        # =====================================================

        people = [
            entity["text"]
            for entity in entities
            if entity["label"] == "PERSON"
        ]

        locations = [
            entity["text"]
            for entity in entities
            if entity["label"] == "LOCATION"
        ]

        vehicles = [
            entity["text"]
            for entity in entities
            if entity["label"] == "VEHICLE"
        ]

        phones = [
            entity["text"]
            for entity in entities
            if entity["label"] == "PHONE"
        ]

        organizations = [
            entity["text"]
            for entity in entities
            if entity["label"] == "ORGANIZATION"
        ]

        amounts = [
            entity["text"]
            for entity in entities
            if entity["label"] == "AMOUNT"
        ]

        # =====================================================
        # Split FIR into sentences
        # =====================================================

        sentences = self._split_sentences(text)

        # =====================================================
        # Analyze every sentence
        # =====================================================

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            sentence_lower = sentence.lower()

            # =================================================
            # Entities appearing in this sentence
            # =================================================

            sentence_people = self._entities_in_sentence(
                people,
                sentence
            )

            sentence_locations = self._entities_in_sentence(
                locations,
                sentence
            )

            sentence_vehicles = self._entities_in_sentence(
                vehicles,
                sentence
            )

            sentence_phones = self._entities_in_sentence(
                phones,
                sentence
            )

            sentence_organizations = self._entities_in_sentence(
                organizations,
                sentence
            )

            sentence_amounts = self._entities_in_sentence(
                amounts,
                sentence
            )

            # =================================================
            # 1. COMMUNICATION
            # =================================================

            if self._contains_keyword(
                sentence_lower,
                self.relationship_keywords[
                    "COMMUNICATED_WITH"
                ]
            ):

                call_count = self._extract_call_count(
                    sentence
                )

                self._add_person_relationships(
                    relationships,
                    sentence_people,
                    "COMMUNICATED_WITH",
                    sentence,
                    call_count=call_count
                )

                # Phone association

                if sentence_phones:

                    for person in sentence_people:

                        for phone in sentence_phones:

                            self._add_relationship(
                                relationships,
                                person,
                                "COMMUNICATED_VIA",
                                phone,
                                sentence
                            )

            # =================================================
            # 2. MEETING
            # =================================================

            if self._contains_keyword(
                sentence_lower,
                self.relationship_keywords["MET"]
            ):

                self._add_person_relationships(
                    relationships,
                    sentence_people,
                    "MET",
                    sentence
                )

                # Meeting location

                for person in sentence_people:

                    for location in sentence_locations:

                        self._add_relationship(
                            relationships,
                            person,
                            "LOCATED_AT",
                            location,
                            sentence
                        )

            # =================================================
            # 3. TRAVEL
            # =================================================

            if self._contains_keyword(
                sentence_lower,
                self.relationship_keywords[
                    "TRAVELLED_WITH"
                ]
            ):

                self._add_person_relationships(
                    relationships,
                    sentence_people,
                    "TRAVELLED_WITH",
                    sentence
                )

                # Person → Vehicle

                for person in sentence_people:

                    for vehicle in sentence_vehicles:

                        self._add_relationship(
                            relationships,
                            person,
                            "USED",
                            vehicle,
                            sentence
                        )

                # Person → Location

                for person in sentence_people:

                    for location in sentence_locations:

                        self._add_relationship(
                            relationships,
                            person,
                            "LOCATED_AT",
                            location,
                            sentence
                        )

            # =================================================
            # 4. MONEY TRANSFER
            # =================================================

            if self._contains_keyword(
                sentence_lower,
                self.relationship_keywords[
                    "TRANSFERRED_TO"
                ]
            ):

                self._add_person_relationships(
                    relationships,
                    sentence_people,
                    "TRANSFERRED_TO",
                    sentence,
                    amounts=sentence_amounts
                )

                # Person → Organization

                if sentence_organizations:

                    for person in sentence_people:

                        for organization in sentence_organizations:

                            relationship = {

                                "source": person,

                                "relationship":
                                    "TRANSFERRED_TO",

                                "target": organization,

                                "evidence": sentence
                            }

                            if sentence_amounts:

                                amount = self._parse_amount(
                                    sentence_amounts[0]
                                )

                                if amount is not None:

                                    relationship["amount"] = amount

                            relationships.append(
                                relationship
                            )

            # =================================================
            # 5. OWNERSHIP
            # =================================================

            if self._contains_keyword(
                sentence_lower,
                self.relationship_keywords["OWNED"]
            ):

                # Person → Vehicle

                for person in sentence_people:

                    for vehicle in sentence_vehicles:

                        self._add_relationship(
                            relationships,
                            person,
                            "OWNED",
                            vehicle,
                            sentence
                        )

                # Person → Organization

                for person in sentence_people:

                    for organization in sentence_organizations:

                        self._add_relationship(
                            relationships,
                            person,
                            "OWNED",
                            organization,
                            sentence
                        )

            # =================================================
            # 6. VEHICLE USAGE
            # =================================================

            if self._contains_keyword(
                sentence_lower,
                self.relationship_keywords["USED"]
            ):

                for person in sentence_people:

                    for vehicle in sentence_vehicles:

                        self._add_relationship(
                            relationships,
                            person,
                            "USED",
                            vehicle,
                            sentence
                        )

            # =================================================
            # 7. GENERAL ASSOCIATION
            # =================================================

            if self._contains_keyword(
                sentence_lower,
                self.relationship_keywords[
                    "ASSOCIATED_WITH"
                ]
            ):

                # Person ↔ Person

                self._add_person_relationships(
                    relationships,
                    sentence_people,
                    "ASSOCIATED_WITH",
                    sentence
                )

                # Person → Organization

                for person in sentence_people:

                    for organization in sentence_organizations:

                        self._add_relationship(
                            relationships,
                            person,
                            "ASSOCIATED_WITH",
                            organization,
                            sentence
                        )

                # Person → Location

                for person in sentence_people:

                    for location in sentence_locations:

                        self._add_relationship(
                            relationships,
                            person,
                            "ASSOCIATED_WITH",
                            location,
                            sentence
                        )

            # =================================================
            # 8. LOCATION ASSOCIATION
            # =================================================

            location_indicators = [

                "near",
                "at",
                "in",
                "inside",
                "outside",
                "from",
                "located at",
                "found at",
                "seen at"
            ]

            if sentence_locations and sentence_people:

                if self._contains_keyword(
                    sentence_lower,
                    location_indicators
                ):

                    for person in sentence_people:

                        for location in sentence_locations:

                            self._add_relationship(
                                relationships,
                                person,
                                "LOCATED_AT",
                                location,
                                sentence
                            )

        # =====================================================
        # Remove duplicate relationships
        # =====================================================

        relationships = self._remove_duplicates(
            relationships
        )

        return relationships

    # =========================================================
    # ADD PERSON-PERSON RELATIONSHIPS
    # =========================================================

    def _add_person_relationships(
        self,
        relationships,
        people,
        relationship_type,
        evidence,
        amounts=None,
        call_count=None
    ):

        if len(people) < 2:
            return

        for i in range(len(people)):

            for j in range(i + 1, len(people)):

                relationship = {

                    "source": people[i],

                    "relationship": relationship_type,

                    "target": people[j],

                    "evidence": evidence
                }

                # ---------------------------------------------
                # Communication call count
                # ---------------------------------------------

                if relationship_type == "COMMUNICATED_WITH":

                    if call_count is None:

                        call_count = self._extract_call_count(
                            evidence
                        )

                    if call_count is not None:

                        # `count` is the public relationship field consumed by
                        # the graph, pattern, correlation, and UI layers.
                        relationship["count"] = call_count

                # ---------------------------------------------
                # Transaction amount
                # ---------------------------------------------

                if (
                    relationship_type == "TRANSFERRED_TO"
                    and amounts
                ):

                    amount = self._parse_amount(
                        amounts[0]
                    )

                    if amount is not None:

                        relationship["amount"] = amount

                relationships.append(
                    relationship
                )

    # =========================================================
    # EXTRACT CALL COUNT
    # =========================================================

    def _extract_call_count(self, text):

        patterns = [

            # 15 times
            r"\b(\d+)\s+times\b",

            # 15 calls
            r"\b(\d+)\s+calls?\b",

            # called 15 times
            r"\bcalled\s+.*?\b(\d+)\s+times\b",

            # contacted 15 times
            r"\bcontacted\s+.*?\b(\d+)\s+times\b"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                return int(
                    match.group(1)
                )

        return None

    # =========================================================
    # PARSE AMOUNT
    # =========================================================

    def _parse_amount(self, amount_text):

        if amount_text is None:
            return None

        text = str(amount_text)

        # Keep digits, commas and decimal point.

        match = re.search(
            r"\d[\d,]*(?:\.\d+)?",
            text
        )

        if not match:
            return None

        numeric_text = match.group(
            0
        ).replace(",", "")

        try:

            value = float(
                numeric_text
            )

            if value.is_integer():

                return int(value)

            return value

        except ValueError:

            return None

    # =========================================================
    # ADD RELATIONSHIP
    # =========================================================

    def _add_relationship(
        self,
        relationships,
        source,
        relationship_type,
        target,
        evidence
    ):

        if not source or not target:
            return

        if source == target:
            return

        relationships.append({

            "source": source,

            "relationship": relationship_type,

            "target": target,

            "evidence": evidence
        })

    # =========================================================
    # FIND ENTITIES IN SENTENCE
    # =========================================================

    def _entities_in_sentence(
        self,
        entities,
        sentence
    ):

        found = []

        sentence_lower = sentence.lower()

        for entity in entities:

            if entity.lower() in sentence_lower:

                found.append(entity)

        # Sort according to position in sentence

        found.sort(
            key=lambda x: sentence_lower.find(
                x.lower()
            )
        )

        return found

    # =========================================================
    # KEYWORD CHECK
    # =========================================================

    def _contains_keyword(
        self,
        text,
        keywords
    ):

        for keyword in keywords:

            pattern = (
                r"\b"
                + re.escape(keyword.lower())
                + r"\b"
            )

            if re.search(
                pattern,
                text
            ):

                return True

        return False

    # =========================================================
    # SENTENCE SPLITTER
    # =========================================================

    def _split_sentences(self, text):

        sentences = re.split(
            r"(?<=[.!?])\s+|\n+",
            text
        )

        return [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

    # =========================================================
    # REMOVE DUPLICATES
    # =========================================================

    def _remove_duplicates(
        self,
        relationships
    ):

        unique = {}

        for relationship in relationships:

            key = (

                relationship["source"].lower(),

                relationship["relationship"],

                relationship["target"].lower()
            )

            if key not in unique:

                unique[key] = relationship

            else:

                existing = unique[key]

                # ---------------------------------------------
                # Preserve different evidence
                # ---------------------------------------------

                if (
                    relationship.get("evidence")
                    and relationship.get("evidence")
                    != existing.get("evidence")
                ):

                    existing["evidence"] = (

                        existing.get(
                            "evidence",
                            ""
                        )

                        + " | "

                        + relationship["evidence"]
                    )

                # ---------------------------------------------
                # Preserve highest call count
                # ---------------------------------------------

                if "count" in relationship:

                    existing["count"] = max(

                        existing.get(
                            "count",
                            0
                        ),

                        relationship["count"]
                    )

                # ---------------------------------------------
                # Preserve highest transaction amount
                # ---------------------------------------------

                if "amount" in relationship:

                    existing["amount"] = max(

                        existing.get(
                            "amount",
                            0
                        ),

                        relationship["amount"]
                    )

        return list(
            unique.values()
        )