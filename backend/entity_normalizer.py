import re


class EntityNormalizer:
    """
    Standardize extracted intelligence entities before relationship extraction.

    The normalizer keeps human-readable values for the UI while applying stable
    formats to identifiers such as phone and vehicle numbers. It does not make
    identity-resolution decisions; aliases remain available for review.
    """

    TYPE_ALIASES = {
        "GPE": "LOCATION",
        "LOC": "LOCATION",
        "FAC": "LOCATION",
        "ORG": "ORGANIZATION",
    }
    SUPPORTED_TYPES = {
        "PERSON",
        "LOCATION",
        "VEHICLE",
        "PHONE",
        "ORGANIZATION",
        "DATE",
        "AMOUNT",
        "CALL_COUNT",
    }

    def normalize(self, entities, text):
        text = str(text or "")
        normalized = []

        # Normalize extractor output first.
        for entity in entities or []:
            item = self._normalize_entity(
                entity,
                default_source="EXTRACTOR",
            )
            if item:
                normalized.append(item)

        # Add reliable rule-based identifiers and analytics values. These
        # patterns make CDR and financial records usable even when NLP misses
        # an entity.
        normalized.extend(self._extract_vehicles(text))
        normalized.extend(self._extract_phones(text))
        normalized.extend(self._extract_dates(text))
        normalized.extend(self._extract_amounts(text))
        normalized.extend(self._extract_call_counts(text))

        normalized = self._remove_invalid(normalized)
        normalized = self._deduplicate(normalized)
        normalized.sort(key=lambda item: self._text_position(item["text"], text))
        return normalized

    def _normalize_entity(self, entity, default_source):
        if not isinstance(entity, dict):
            return None

        raw_text = self._clean_text(entity.get("text", ""))
        entity_type = self._canonical_type(entity.get("label"))
        source = entity.get("source") or default_source

        if not raw_text or entity_type not in self.SUPPORTED_TYPES:
            return None

        if entity_type == "PERSON":
            raw_text = self._normalize_person(raw_text)
        elif entity_type == "LOCATION":
            raw_text = self._normalize_location(raw_text)
        elif entity_type == "ORGANIZATION":
            raw_text = self._normalize_organization(raw_text)
        elif entity_type == "VEHICLE":
            raw_text = self._normalize_vehicle(raw_text)
        elif entity_type == "PHONE":
            raw_text = self._normalize_phone(raw_text)
        elif entity_type == "DATE":
            raw_text = self._normalize_date(raw_text)
        elif entity_type == "AMOUNT":
            raw_text = self._normalize_amount(raw_text)
        elif entity_type == "CALL_COUNT":
            raw_text = self._normalize_call_count(raw_text)

        if not raw_text:
            return None

        return {
            "text": raw_text,
            "label": entity_type,
            "source": source,
        }

    def _extract_vehicles(self, text):
        pattern = r"\b[A-Z]{2}[-\s]?\d{1,2}[-\s]?[A-Z]{1,3}[-\s]?\d{4}\b"
        return self._rule_entities(text, pattern, "VEHICLE")

    def _extract_phones(self, text):
        patterns = [
            r"(?<!\d)[6-9]\d{9}(?!\d)",
            r"\+91[-\s]?[6-9]\d{9}",
            r"(?<!\d)0[6-9]\d{9}(?!\d)",
        ]
        return [
            item
            for pattern in patterns
            for item in self._rule_entities(text, pattern, "PHONE")
        ]

    def _extract_dates(self, text):
        patterns = [
            r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|"
            r"August|September|October|November|December)(?:\s+\d{4})?\b",
            r"\b(?:January|February|March|April|May|June|July|August|"
            r"September|October|November|December)\s+\d{1,2}"
            r"(?:,?\s+\d{4})?\b",
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
            r"\b\d{4}-\d{1,2}-\d{1,2}\b",
        ]
        return [
            item
            for pattern in patterns
            for item in self._rule_entities(text, pattern, "DATE")
        ]

    def _extract_amounts(self, text):
        patterns = [
            r"₹\s*\d+(?:,\d+)*(?:\.\d+)?",
            r"\bRs\.?\s*\d+(?:,\d+)*(?:\.\d+)?",
            r"\b\d+(?:,\d+)*(?:\.\d+)?\s*INR\b",
            r"\b\d+(?:,\d+)*(?:\.\d+)?\s*(?:rupee|rupees)\b",
        ]
        return [
            item
            for pattern in patterns
            for item in self._rule_entities(text, pattern, "AMOUNT")
        ]

    def _extract_call_counts(self, text):
        patterns = [
            r"\b(\d+)\s+times\b",
            r"\b(\d+)\s+calls?\b",
        ]
        items = []
        for pattern in patterns:
            for match in re.findall(pattern, text, re.IGNORECASE):
                item = self._normalize_entity(
                    {"text": match, "label": "CALL_COUNT", "source": "RULE"},
                    "RULE",
                )
                if item:
                    items.append(item)
        return items

    def _rule_entities(self, text, pattern, label):
        items = []
        for match in re.findall(pattern, text, re.IGNORECASE):
            item = self._normalize_entity(
                {"text": match, "label": label, "source": "RULE"},
                "RULE",
            )
            if item:
                items.append(item)
        return items

    def _remove_invalid(self, entities):
        valid = []
        for entity in entities:
            text = entity["text"]
            label = entity["label"]

            if label == "PERSON" and self._is_invalid_person(text):
                continue
            if label == "LOCATION" and self._is_invalid_location(text):
                continue
            if label == "ORGANIZATION" and self._is_currency_word(text):
                continue

            valid.append(entity)
        return valid

    @staticmethod
    def _deduplicate(entities):
        unique = {}
        for entity in entities:
            key = (entity["label"], entity["text"].casefold())
            if key not in unique:
                unique[key] = entity
            elif entity["source"] == "RULE":
                # A rule-confirmed identifier is stronger than a generic NLP
                # label when the same canonical value appears twice.
                unique[key] = entity
        return list(unique.values())

    @staticmethod
    def _canonical_type(value):
        value = str(value or "").upper().strip()
        return EntityNormalizer.TYPE_ALIASES.get(value, value)

    @staticmethod
    def _clean_text(value):
        value = re.sub(r"\s+", " ", str(value or "")).strip()
        return value.strip(".,!?;:\"'()[]{}")

    def _normalize_person(self, value):
        value = re.sub(r"\s+", " ", value).strip()
        return None if self._is_invalid_person(value) else value

    def _normalize_location(self, value):
        value = re.sub(r"\s+", " ", value).strip()
        return None if self._is_invalid_location(value) else value

    def _normalize_organization(self, value):
        value = re.sub(r"\s+", " ", value).strip()
        return None if self._is_currency_word(value) else value

    @staticmethod
    def _normalize_vehicle(value):
        value = re.sub(r"[-\s]", "", value).upper()
        if re.fullmatch(r"[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{4}", value):
            return value
        return None

    @staticmethod
    def _normalize_phone(value):
        digits = re.sub(r"\D", "", value)
        if digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]
        elif digits.startswith("0") and len(digits) == 11:
            digits = digits[1:]
        return digits if re.fullmatch(r"[6-9]\d{9}", digits) else None

    @staticmethod
    def _normalize_date(value):
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def _normalize_amount(value):
        value = re.sub(r"\s+", " ", value).strip()
        match = re.search(r"\d[\d,]*(?:\.\d+)?", value)
        if not match:
            return None
        # Keep the original textual representation (for example, "75000 INR")
        # so relationship extraction can locate it in the source sentence.
        # The relationship extractor converts it to a numeric amount later.
        return value

    @staticmethod
    def _normalize_call_count(value):
        match = re.search(r"\d+", str(value))
        return match.group(0) if match else None

    @staticmethod
    def _text_position(entity_text, document_text):
        position = document_text.casefold().find(entity_text.casefold())
        return position if position >= 0 else len(document_text) + 1

    @staticmethod
    def _is_currency_word(text):
        return text.upper().strip() in {
            "INR", "RS", "RS.", "RUPEE", "RUPEES", "₹", "USD",
            "DOLLAR", "DOLLARS", "EUR", "EURO", "EUROS", "GBP",
            "POUND", "POUNDS",
        }

    @staticmethod
    def _is_invalid_person(text):
        return text.casefold() in {
            "police", "officer", "inspector", "constable", "complainant",
            "victim", "suspect", "accused", "witness", "unknown person",
        }

    @staticmethod
    def _is_invalid_location(text):
        return text.casefold() in {
            "location", "place", "area", "address", "city", "district",
        }