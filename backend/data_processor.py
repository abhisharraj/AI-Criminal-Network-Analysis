import os
import pandas as pd

from backend.entity_extractor import EntityExtractor
from backend.entity_normalizer import EntityNormalizer
from backend.relationship_extractor import RelationshipExtractor


class DataProcessor:

    def __init__(self, file_path):

        self.file_path = file_path

        self.extractor = EntityExtractor()

        self.normalizer = EntityNormalizer()

        self.relationship_extractor = RelationshipExtractor()

    def load_data(self):

        return pd.read_csv(self.file_path)

    def process_data(self):

        df = self.load_data()

        processed_records = []

        for _, row in df.iterrows():

            text = row["text"]

            # Step 1: Extract entities
            entities = self.extractor.extract_entities(text)

            # Step 2: Normalize entities
            entities = self.normalizer.normalize(
                entities,
                text
            )

            # Step 3: Extract relationships
            relationships = (
                self.relationship_extractor
                .extract_relationships(
                    text,
                    entities
                )
            )

            # Step 4: Store complete record
            processed_records.append({

                "record_id": row["record_id"],

                "record_type": row["record_type"],

                "source": row["source"],

                "text": text,

                "entities": entities,

                "relationships": relationships

            })

        return processed_records


if __name__ == "__main__":

    # -----------------------------------------
    # Automatically locate sample_data.csv
    # -----------------------------------------

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

    # -----------------------------------------
    # Process data
    # -----------------------------------------

    processor = DataProcessor(data_file)

    records = processor.process_data()

    # -----------------------------------------
    # Display results
    # -----------------------------------------

    for record in records:

        print("\n-------------------------")

        print("Record:", record["record_id"])

        print("Type:", record["record_type"])

        print("Entities:")

        for entity in record["entities"]:

            print(
                f"  {entity['text']} -> "
                f"{entity['label']}"
            )

        print("Relationships:")

        for relationship in record["relationships"]:

            print(
                f"  {relationship['source']} "
                f"--{relationship['relationship']}--> "
                f"{relationship['target']}"
            )

            if "count" in relationship:

                print(
                    f"      Call Count: "
                    f"{relationship['count']}"
                )

            if "amount" in relationship:

                print(
                    f"      Amount: "
                    f"₹{relationship['amount']}"
                )