import re
import spacy


class EntityExtractor:
    """
    Extract entities from FIRs, CDRs, financial records, and surveillance text.

    Uses:
    1. spaCy NER for general entity recognition
    2. Rule-based extraction for Indian names, locations, organizations,
       phones, vehicles, dates, money, application numbers, and roles
    3. Context-aware filtering to reduce false positives
    """

    MONTHS = (
        "January|February|March|April|May|June|July|August|"
        "September|October|November|December"
    )

    HONORIFICS = {
        "mr", "mr.", "mrs", "mrs.", "ms", "ms.", "miss",
        "smt", "smt.", "shri", "shri.", "sri", "sri.",
        "dr", "dr."
    }

    ROLE_WORDS = {
        "president",
        "representative",
        "authorized representative",
        "officer",
        "inspector",
        "sub-inspector",
        "superintendent",
        "director",
        "manager",
        "chairman",
        "secretary",
        "commissioner",
        "accused",
        "complainant",
        "witness",
        "victim",
        "staff",
        "employee",
        "public servant",
    }

    FALSE_ORGANIZATIONS = {
        "complaint",
        "complaints",
        "application",
        "applications",
        "verification",
        "report",
        "reports",
        "file",
        "files",
        "document",
        "documents",
        "office",
        "department",
        "officer",
        "staff",
        "employee",
        "advantage",
        "amount",
        "certificate",
        "registration",
        "case",
        "matter",
        "same day",
        "police",
        "patna",
        "saharsa",
        "bihar",
        "delhi",
        "lucknow",
        "india",
    }

    GENERIC_LOCATIONS = {
        "location",
        "place",
        "area",
        "address",
        "city",
        "district",
        "state",
        "country",
        "office",
        "department",
    }

    LOCATION_WORDS = {
        "patna",
        "saharsa",
        "bihar",
        "delhi",
        "mumbai",
        "kolkata",
        "lucknow",
        "gorakhpur",
        "varanasi",
        "prayagraj",
        "ranchi",
        "jaipur",
        "kanpur",
        "noida",
        "gurugram",
        "gaya",
        "muzaffarpur",
        "bhagalpur",
        "darbhanga",
    }

    LOCATION_SUFFIXES = (
        "station",
        "railway station",
        "airport",
        "junction",
        "road",
        "market",
        "hospital",
        "college",
        "school",
        "office",
        "temple",
        "hotel",
        "police station",
        "court",
        "jail",
        "village",
        "town",
        "district",
    )

    ORGANIZATION_KEYWORDS = (
        "ngo",
        "organization",
        "organisation",
        "sansthan",
        "foundation",
        "association",
        "society",
        "trust",
        "bank",
        "company",
        "corporation",
        "department",
        "bureau",
        "office",
        "commission",
        "authority",
        "ministry",
        "income tax",
        "central bureau",
        "cbi",
        "acb",
    )

    def __init__(self, model_name="en_core_web_sm"):
        try:
            self.nlp = spacy.load(model_name)
            self.model_available = True
        except OSError:
            self.nlp = spacy.blank("en")
            self.model_available = False

    def extract_entities(self, text):
        text = str(text or "").strip()

        if not text:
            return []

        entities = {}

        # General NLP
        self._extract_nlp_entities(text, entities)

        # Domain-specific rules
        self._extract_honorific_people(text, entities)
        self._extract_contextual_people(text, entities)
        self._extract_locations(text, entities)
        self._extract_organizations(text, entities)
        self._extract_roles(text, entities)

        # Structured entities
        self._extract_vehicles(text, entities)
        self._extract_phones(text, entities)
        self._extract_dates(text, entities)
        self._extract_amounts(text, entities)
        self._extract_application_numbers(text, entities)
        self._extract_call_counts(text, entities)

        return self._clean_and_sort(entities, text)

    # ------------------------------------------------------------------
    # NLP ENTITY EXTRACTION
    # ------------------------------------------------------------------

    def _extract_nlp_entities(self, text, entities):
        if not self.model_available:
            return

        doc = self.nlp(text)

        for entity in doc.ents:
            value = self._clean_text(entity.text)
            label = entity.label_

            if not value:
                continue

            if label == "PERSON":
                self._add_entity(
                    entities,
                    value,
                    "PERSON",
                    "NLP"
                )

            elif label in {"GPE", "LOC", "FAC"}:
                self._add_entity(
                    entities,
                    value,
                    "LOCATION",
                    "NLP"
                )

            elif label == "ORG":
                if self._is_valid_organization(value):
                    self._add_entity(
                        entities,
                        value,
                        "ORGANIZATION",
                        "NLP"
                    )

            elif label == "DATE":
                self._add_entity(
                    entities,
                    value,
                    "DATE",
                    "NLP"
                )

            elif label == "MONEY":
                self._add_entity(
                    entities,
                    value,
                    "AMOUNT",
                    "NLP"
                )

    # ------------------------------------------------------------------
    # PEOPLE
    # ------------------------------------------------------------------

    def _extract_honorific_people(self, text, entities):
        """
        Detect Indian names introduced by:
        Shri, Smt., Mr., Ms., Mrs., Dr., etc.

        Examples:
        Smt. Sunanda Kumar
        Shri Niraj Kumar
        Ms. Jyoti Mishra
        """
        name_pattern = (
            r"([A-Z][a-z]+"
            r"(?:\s+[A-Z]\.)?"
            r"(?:\s+[A-Z][a-z]+)+)"
        )

        pattern = (
            r"\b(?:Mr\.?|Mrs\.?|Ms\.?|Miss|Smt\.?|Shri|Sri|Dr\.?)"
            r"\s+"
            + name_pattern
        )

        for match in re.finditer(pattern, text):
            value = self._clean_text(match.group(1))

            if self._looks_like_person_name(value):
                self._add_entity(
                    entities,
                    value,
                    "PERSON",
                    "RULE"
                )

    def _extract_contextual_people(self, text, entities):
        """
        Detect names from common FIR/intelligence language.
        """

        name = (
            r"([A-Z][a-z]+"
            r"(?:\s+[A-Z]\.)?"
            r"(?:\s+[A-Z][a-z]+)+)"
        )

        patterns = [
            rf"\b(?:accused|suspect|witness|victim|complainant)\s+{name}",
            rf"\b{name}\s+(?:called|contacted|met|visited|travelled|"
            rf"traveled|transferred|paid|sent|used|owned|demanded)\b",
            rf"\b(?:with|to|by|from)\s+{name}\b",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                value = self._clean_text(match.group(1))

                if self._looks_like_person_name(value):
                    self._add_entity(
                        entities,
                        value,
                        "PERSON",
                        "RULE"
                    )

    # ------------------------------------------------------------------
    # LOCATIONS
    # ------------------------------------------------------------------

    def _extract_locations(self, text, entities):
        """
        Extract locations from:
        - known Indian city/state names
        - location suffixes
        - contextual phrases
        - comma-separated location references
        """

        # Known locations
        for location in self.LOCATION_WORDS:
            pattern = rf"\b{re.escape(location)}\b"

            for match in re.finditer(
                pattern,
                text,
                re.IGNORECASE
            ):
                value = self._clean_text(match.group(0))

                self._add_entity(
                    entities,
                    value.title(),
                    "LOCATION",
                    "RULE"
                )

        # Places such as:
        # Gorakhpur Railway Station
        # Patna Police Station
        location_suffix_pattern = (
            r"\b[A-Z][A-Za-z]+"
            r"(?:\s+[A-Z][A-Za-z]+){0,4}"
            r"\s+(?:Railway Station|Station|Airport|Junction|Road|"
            r"Market|Hospital|College|School|Office|Temple|Hotel|"
            r"Police Station|Court|Jail)\b"
        )

        for match in re.finditer(
            location_suffix_pattern,
            text
        ):
            value = self._clean_text(match.group(0))

            if not self._is_generic_location(value):
                self._add_entity(
                    entities,
                    value,
                    "LOCATION",
                    "RULE"
                )

        # Contextual locations
        contextual_pattern = (
            r"\b(?:near|at|inside|outside|from|in|of)\s+"
            r"([A-Z][A-Za-z]+"
            r"(?:\s+[A-Z][A-Za-z]+){0,4})"
        )

        for match in re.finditer(
            contextual_pattern,
            text
        ):
            value = self._clean_text(match.group(1))

            if self._looks_like_location(value):
                self._add_entity(
                    entities,
                    value,
                    "LOCATION",
                    "RULE"
                )

        # Combinations such as:
        # Saharsa, Bihar
        # Patna, Bihar
        comma_location_pattern = (
            r"\b([A-Z][A-Za-z]+)"
            r",\s*"
            r"([A-Z][A-Za-z]+)\b"
        )

        for match in re.finditer(
            comma_location_pattern,
            text
        ):
            first = match.group(1)
            second = match.group(2)

            if (
                first.casefold() in self.LOCATION_WORDS
                or second.casefold() in self.LOCATION_WORDS
            ):
                self._add_entity(
                    entities,
                    first,
                    "LOCATION",
                    "RULE"
                )
                self._add_entity(
                    entities,
                    second,
                    "LOCATION",
                    "RULE"
                )

    # ------------------------------------------------------------------
    # ORGANIZATIONS
    # ------------------------------------------------------------------

    def _extract_organizations(self, text, entities):
        patterns = [
            # M/s XYZ
            r"\bM/s\.?\s+([A-Z][A-Za-z0-9&.,()' -]{2,80})",

            # Names ending in common organization words
            r"\b([A-Z][A-Za-z0-9&.,()' -]{2,80}"
            r"\s+(?:Ltd\.?|Limited|Pvt\.?\s*Ltd\.?|"
            r"Bank|Company|Corporation|Foundation|Association|"
            r"Society|Trust|Sansthan))\b",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                value = self._clean_text(match.group(1))

                if self._is_valid_organization(value):
                    self._add_entity(
                        entities,
                        value,
                        "ORGANIZATION",
                        "RULE"
                    )

        # Explicit organizations from common institutional language
        explicit_pattern = (
            r"\b(?:CBI|ACB|NGO|"
            r"Income Tax Department|"
            r"Central Bureau of Investigation|"
            r"Income Tax Office)\b"
        )

        for match in re.finditer(
            explicit_pattern,
            text,
            re.IGNORECASE
        ):
            value = self._clean_text(match.group(0))

            self._add_entity(
                entities,
                value,
                "ORGANIZATION",
                "RULE"
            )

    # ------------------------------------------------------------------
    # ROLES
    # ------------------------------------------------------------------

    def _extract_roles(self, text, entities):
        role_pattern = (
            r"\b(?:Income Tax Officer|"
            r"Sub-Inspector of Police|"
            r"Police Inspector|"
            r"Inspector|"
            r"Sub-Inspector|"
            r"President|"
            r"Authorized Representative|"
            r"Public Servant|"
            r"Director|"
            r"Manager|"
            r"Commissioner|"
            r"Officer)\b"
        )

        for match in re.finditer(
            role_pattern,
            text,
            re.IGNORECASE
        ):
            value = self._clean_text(match.group(0))

            self._add_entity(
                entities,
                value,
                "ROLE",
                "RULE"
            )

    # ------------------------------------------------------------------
    # VEHICLES
    # ------------------------------------------------------------------

    def _extract_vehicles(self, text, entities):
        pattern = (
            r"\b[A-Z]{2}[-\s]?\d{1,2}"
            r"[-\s]?[A-Z]{1,3}"
            r"[-\s]?\d{4}\b"
        )

        for match in re.finditer(
            pattern,
            text,
            re.IGNORECASE
        ):
            value = re.sub(
                r"[-\s]",
                "",
                match.group(0)
            ).upper()

            self._add_entity(
                entities,
                value,
                "VEHICLE",
                "RULE"
            )

    # ------------------------------------------------------------------
    # PHONES
    # ------------------------------------------------------------------

    def _extract_phones(self, text, entities):
        patterns = [
            r"(?<!\d)[6-9]\d{9}(?!\d)",
            r"\+91[-\s]?[6-9]\d{9}",
            r"(?<!\d)0[6-9]\d{9}(?!\d)",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                value = re.sub(
                    r"\D",
                    "",
                    match.group(0)
                )

                if value.startswith("91") and len(value) == 12:
                    value = value[2:]

                elif value.startswith("0") and len(value) == 11:
                    value = value[1:]

                if re.fullmatch(r"[6-9]\d{9}", value):
                    self._add_entity(
                        entities,
                        value,
                        "PHONE",
                        "RULE"
                    )

    # ------------------------------------------------------------------
    # DATES
    # ------------------------------------------------------------------

    def _extract_dates(self, text, entities):
        patterns = [
            rf"\b\d{{1,2}}\s+(?:{self.MONTHS})"
            rf"(?:\s+\d{{4}})?\b",

            rf"\b(?:{self.MONTHS})\s+\d{{1,2}}"
            rf"(?:,?\s+\d{{4}})?\b",

            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",

            r"\b\d{4}-\d{1,2}-\d{1,2}\b",
        ]

        for pattern in patterns:
            for match in re.finditer(
                pattern,
                text,
                re.IGNORECASE
            ):
                value = re.sub(
                    r"\s+",
                    " ",
                    match.group(0)
                ).strip()

                self._add_entity(
                    entities,
                    value,
                    "DATE",
                    "RULE"
                )

    # ------------------------------------------------------------------
    # AMOUNTS / MONEY
    # ------------------------------------------------------------------

    def _extract_amounts(self, text, entities):
        """
        Handles normal and OCR-corrupted Indian currency forms.

        Examples:
        ₹75,000
        Rs. 75,000
        INR 75,000
        75,000 rupees
        %75,000
        ¥5,000
        40,000/-
        """

        patterns = [
            r"(?:₹|Rs\.?|INR|%|¥|\$)\s*"
            r"\d+(?:,\d{2,3})*(?:\.\d+)?"
            r"(?:/-)?",

            r"\b\d+(?:,\d{2,3})*(?:\.\d+)?"
            r"\s*(?:INR|rupees?|Rs\.?)"
            r"(?:/-)?\b",

            r"\b\d+(?:,\d{2,3})*(?:\.\d+)?/-",
        ]

        for pattern in patterns:
            for match in re.finditer(
                pattern,
                text,
                re.IGNORECASE
            ):
                value = self._clean_text(match.group(0))

                self._add_entity(
                    entities,
                    value,
                    "AMOUNT",
                    "RULE"
                )

    # ------------------------------------------------------------------
    # APPLICATION NUMBERS
    # ------------------------------------------------------------------

    def _extract_application_numbers(self, text, entities):
        patterns = [
            r"\bApplication\s+No\.?\s*"
            r"([A-Za-z0-9./_-]+)",

            r"\bApplication\s+Number\s*"
            r"([A-Za-z0-9./_-]+)",
        ]

        for pattern in patterns:
            for match in re.finditer(
                pattern,
                text,
                re.IGNORECASE
            ):
                value = self._clean_text(match.group(1))

                self._add_entity(
                    entities,
                    value,
                    "APPLICATION",
                    "RULE"
                )

    # ------------------------------------------------------------------
    # CALL COUNTS
    # ------------------------------------------------------------------

    def _extract_call_counts(self, text, entities):
        patterns = [
            r"\b(\d+)\s+times\b",
            r"\b(\d+)\s+calls?\b",
        ]

        for pattern in patterns:
            for match in re.finditer(
                pattern,
                text,
                re.IGNORECASE
            ):
                self._add_entity(
                    entities,
                    match.group(1),
                    "CALL_COUNT",
                    "RULE"
                )

    # ------------------------------------------------------------------
    # ENTITY STORAGE
    # ------------------------------------------------------------------

    def _add_entity(
        self,
        entities,
        text,
        label,
        source
    ):
        text = self._clean_text(text)

        if not text:
            return

        if label == "ORGANIZATION":
            if not self._is_valid_organization(text):
                return

        if label == "LOCATION":
            if self._is_generic_location(text):
                return

        key = (
            text.casefold(),
            label
        )

        # RULE overrides NLP when both identify the same entity.
        if (
            key not in entities
            or source == "RULE"
        ):
            entities[key] = {
                "text": text,
                "label": label,
                "source": source
            }

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------

    def _is_valid_organization(self, value):
        normalized = value.casefold().strip()

        if normalized in self.FALSE_ORGANIZATIONS:
            return False

        if self._is_currency_word(value):
            return False

        # Locations should not become organizations.
        if normalized in self.LOCATION_WORDS:
            return False

        return True

    def _looks_like_person_name(self, value):
        words = value.split()

        if len(words) < 2:
            return False

        if any(
            word.casefold().rstrip(".")
            in self.HONORIFICS
            for word in words
        ):
            return False

        if self._looks_like_location(value):
            return False

        if any(
            word.casefold() in self.ROLE_WORDS
            for word in words
        ):
            return False

        return all(
            re.fullmatch(
                r"[A-Za-z]+(?:\.)?",
                word
            )
            for word in words
        )

    def _looks_like_location(self, value):
        normalized = value.casefold().strip()

        if normalized in self.LOCATION_WORDS:
            return True

        if normalized in self.GENERIC_LOCATIONS:
            return True

        return normalized.endswith(
            self.LOCATION_SUFFIXES
        )

    def _is_generic_location(self, value):
        return (
            value.casefold().strip()
            in self.GENERIC_LOCATIONS
        )

    # ------------------------------------------------------------------
    # CLEANING
    # ------------------------------------------------------------------

    def _clean_and_sort(
        self,
        entities,
        text
    ):
        cleaned = []

        for entity in entities.values():
            value = self._clean_text(
                entity["text"]
            )

            if not value:
                continue

            if (
                entity["label"] == "ORGANIZATION"
                and not self._is_valid_organization(value)
            ):
                continue

            cleaned.append({
                **entity,
                "text": value
            })

        return sorted(
            cleaned,
            key=lambda item: self._position(
                item["text"],
                text
            )
        )

    @staticmethod
    def _clean_text(value):
        value = re.sub(
            r"\s+",
            " ",
            str(value or "")
        ).strip()

        return value.strip(
            ".,!?;:\\\"'()[]{}"
        )

    @staticmethod
    def _position(value, text):
        position = text.casefold().find(
            value.casefold()
        )

        return (
            position
            if position >= 0
            else len(text) + 1
        )

    @staticmethod
    def _is_currency_word(value):
        return (
            value.upper().strip()
            in {
                "INR",
                "RS",
                "RS.",
                "RUPEE",
                "RUPEES",
                "₹",
                "USD",
                "DOLLAR",
                "DOLLARS",
                "EUR",
                "EURO",
                "EUROS",
                "GBP",
                "POUND",
                "POUNDS",
            }
        )