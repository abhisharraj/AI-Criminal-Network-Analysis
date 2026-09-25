import os
import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.data_processor import DataProcessor
from backend.graph_builder import GraphBuilder
from backend.investigation_engine import InvestigationEngine
from backend.fir_parser import FIRParser
from backend.entity_extractor import EntityExtractor
from backend.entity_normalizer import EntityNormalizer
from backend.relationship_extractor import RelationshipExtractor


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="AI-Powered Criminal Network Analysis System",
    description="Investigator decision-support system for criminal network analysis.",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",

        # Deployed frontend
        "https://ai-criminal-network-analysis-hello-309r.onrender.com",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# =========================================================
# INITIALIZE COMPONENTS
# =========================================================

fir_parser = FIRParser()

entity_extractor = EntityExtractor()

entity_normalizer = EntityNormalizer()

relationship_extractor = RelationshipExtractor()


# =========================================================
# SAMPLE DATA
# =========================================================

backend_folder = os.path.dirname(
    os.path.abspath(__file__)
)

project_folder = os.path.dirname(
    backend_folder
)

sample_data_file = os.path.join(
    project_folder,
    "data",
    "sample_data.csv"
)


# =========================================================
# GLOBAL CURRENT INVESTIGATION
# =========================================================

# These variables represent the investigation currently
# displayed by the frontend.

records = []

graph = None

engine = None

current_investigation = {
    "type": "DEMO",
    "name": "Sample Investigation",
    "record_id": None
}


# =========================================================
# LOAD INITIAL SAMPLE DATA
# =========================================================

def load_sample_investigation():

    global records
    global graph
    global engine
    global current_investigation

    processor = DataProcessor(
        sample_data_file
    )

    records = processor.process_data()

    builder = GraphBuilder()

    graph = builder.build(
        records
    )

    engine = InvestigationEngine(
        records,
        graph
    )

    current_investigation = {
        "type": "DEMO",
        "name": "Sample Investigation",
        "record_id": None
    }


# Load sample data when server starts

load_sample_investigation()


# =========================================================
# PROCESS UPLOADED FIR
# =========================================================

def process_uploaded_fir(
    text,
    record_id,
    file_name
):

    # -----------------------------------------------------
    # 1. Extract entities
    # -----------------------------------------------------

    extracted_entities = (
        entity_extractor.extract_entities(
            text
        )
    )

    # -----------------------------------------------------
    # 2. Normalize entities
    # -----------------------------------------------------

    normalized_entities = (
        entity_normalizer.normalize(
            extracted_entities,
            text
        )
    )

    # -----------------------------------------------------
    # 3. Extract relationships
    # -----------------------------------------------------

    relationships = (
        relationship_extractor.extract_relationships(
            text,
            normalized_entities
        )
    )

    print("\n========== DEBUG RELATIONSHIPS ==========")
    for relationship in relationships:
        print(relationship)
    print("=========================================\n")

    # -----------------------------------------------------
    # 4. Create record
    # -----------------------------------------------------

    record = {

        "record_id": record_id,

        "record_type": "FIR",

        "source": file_name,

        "text": text,

        "entities": normalized_entities,

        "relationships": relationships

    }

    return record


# =========================================================
# BUILD INVESTIGATION FROM RECORDS
# =========================================================

def rebuild_analysis(
    updated_records,
    investigation_type="CUSTOM",
    investigation_name="Current Investigation",
    record_id=None
):

    global records
    global graph
    global engine
    global current_investigation

    # -----------------------------------------------------
    # Replace current investigation
    # -----------------------------------------------------

    records = updated_records

    # -----------------------------------------------------
    # Build completely new graph
    # -----------------------------------------------------

    builder = GraphBuilder()

    graph = builder.build(
        records
    )

    # -----------------------------------------------------
    # Create new investigation engine
    # -----------------------------------------------------

    engine = InvestigationEngine(
        records,
        graph
    )

    # -----------------------------------------------------
    # Store investigation information
    # -----------------------------------------------------

    current_investigation = {

        "type": investigation_type,

        "name": investigation_name,

        "record_id": record_id

    }


# =========================================================
# ROOT ENDPOINT
# =========================================================

@app.get("/")
def root():

    return {

        "message": "AI-Powered Criminal Network Analysis System",

        "status": "online",

        "investigation": current_investigation

    }


# =========================================================
# CURRENT INVESTIGATION
# =========================================================

@app.get("/api/investigation")
def get_current_investigation():

    return {

        "success": True,

        "investigation": current_investigation

    }


# =========================================================
# NETWORK SUMMARY
# =========================================================

@app.get("/api/summary")
def get_summary():

    if engine is None:

        raise HTTPException(
            status_code=500,
            detail="Investigation engine is not initialized."
        )

    summary = engine.get_network_summary()

    return {

        "success": True,

        "investigation": current_investigation,

        "summary": summary

    }


# =========================================================
# KEY ENTITIES
# =========================================================

@app.get("/api/key-entities")
def get_key_entities():

    if engine is None:

        raise HTTPException(
            status_code=500,
            detail="Investigation engine is not initialized."
        )

    key_entities = engine.get_key_entities()

    return {

        "success": True,

        "investigation": current_investigation,

        "key_entities": key_entities

    }


# =========================================================
# PATTERNS
# =========================================================

@app.get("/api/patterns")
def get_patterns():

    if engine is None:

        raise HTTPException(
            status_code=500,
            detail="Investigation engine is not initialized."
        )

    patterns = engine.get_patterns()

    return {

        "success": True,

        "investigation": current_investigation,

        "patterns": patterns

    }


# =========================================================
# CORRELATIONS
# =========================================================

@app.get("/api/correlations")
def get_correlations():

    if engine is None:

        raise HTTPException(
            status_code=500,
            detail="Investigation engine is not initialized."
        )

    correlations = engine.get_correlations()

    return {

        "success": True,

        "investigation": current_investigation,

        "correlations": correlations

    }


# =========================================================
# EVIDENCE
# =========================================================

@app.get("/api/evidence/{entity_name}")
def get_entity_evidence(
    entity_name: str
):

    if engine is None:

        raise HTTPException(
            status_code=500,
            detail="Investigation engine is not initialized."
        )

    evidence = engine.evidence_tracker.get_entity_evidence(
        entity_name
    )

    return {

        "success": True,

        "investigation": current_investigation,

        "entity": entity_name,

        "evidence": evidence

    }


# =========================================================
# NETWORK GRAPH
# =========================================================

@app.get("/api/network")
def get_network():

    if graph is None:

        raise HTTPException(
            status_code=500,
            detail="Graph is not initialized."
        )

    nodes = []

    edges = []

    # -----------------------------------------------------
    # Nodes
    # -----------------------------------------------------

    for node, data in graph.nodes(
        data=True
    ):

        nodes.append({

            "id": node,

            "label": node,

            "type": data.get(
                "type",
                "UNKNOWN"
            )

        })

    # -----------------------------------------------------
    # Edges
    # -----------------------------------------------------

    for index, (
        source,
        target,
        data
    ) in enumerate(
        graph.edges(
            data=True
        )
    ):

        edge = {

            "id": f"{source}-{target}-{index}",

            "source": source,

            "target": target,

            "relationship": data.get(
                "relationship",
                "UNKNOWN"
            )

        }

        # Call count

        if "count" in data:

            edge["count"] = data["count"]

        # Financial amount

        if "amount" in data:

            edge["amount"] = data["amount"]

        edges.append(
            edge
        )

    return {

        "success": True,

        "investigation": current_investigation,

        "nodes": nodes,

        "edges": edges,

        "network_summary": {

            "total_entities":
                graph.number_of_nodes(),

            "total_relationships":
                graph.number_of_edges()

        }

    }


# =========================================================
# UPLOAD FIR
# =========================================================

@app.post("/api/upload-fir")
async def upload_fir(
    file: UploadFile = File(...)
):

    # -----------------------------------------------------
    # Validate filename
    # -----------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected."
        )

    file_extension = os.path.splitext(
        file.filename
    )[1].lower()

    # -----------------------------------------------------
    # Validate file type
    # -----------------------------------------------------

    if file_extension not in {
        ".txt",
        ".pdf"
    }:

        raise HTTPException(

            status_code=400,

            detail=(
                "Unsupported file type. "
                "Please upload a TXT or PDF file."
            )

        )

    temporary_file = None

    try:

        # -------------------------------------------------
        # Save uploaded file temporarily
        # -------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension
        ) as temp:

            temporary_file = temp.name

            file_content = await file.read()

            temp.write(
                file_content
            )

        # -------------------------------------------------
        # Extract text
        # -------------------------------------------------

        extracted_text = (
            fir_parser.extract_text(
                temporary_file
            )
        )

        if not extracted_text:

            raise HTTPException(

                status_code=400,

                detail=(
                    "Could not extract text "
                    "from the uploaded FIR."
                )

            )

        # -------------------------------------------------
        # Create unique record ID
        # -------------------------------------------------

        record_id = (
            f"UPLOAD-{file.filename}"
        )

        # -------------------------------------------------
        # Process FIR
        # -------------------------------------------------

        uploaded_record = (
            process_uploaded_fir(

                extracted_text,

                record_id,

                file.filename

            )
        )

        # =================================================
        # IMPORTANT
        # =================================================
        #
        # Replace the current investigation.
        #
        # We DO NOT do:
        #
        # records + [uploaded_record]
        #
        # because that would mix the sample dataset
        # with the uploaded FIR.
        #
        # =================================================

        rebuild_analysis(

            updated_records=[
                uploaded_record
            ],

            investigation_type="FIR",

            investigation_name=file.filename,

            record_id=record_id

        )

        # -------------------------------------------------
        # Get analysis for uploaded FIR only
        # -------------------------------------------------

        summary = (
            engine.get_network_summary()
        )

        key_entities = (
            engine.get_key_entities()
        )

        patterns = (
            engine.get_patterns()
        )

        correlations = (
            engine.get_correlations()
        )

        # -------------------------------------------------
        # Return complete result
        # -------------------------------------------------

        return {

            "success": True,

            "file_name": file.filename,

            "file_type": file_extension,

            "text_length": len(
                extracted_text
            ),

            "extracted_text":
                extracted_text,

            "entities":
                uploaded_record[
                    "entities"
                ],

            "relationships":
                uploaded_record[
                    "relationships"
                ],

            "network_summary": {

                "total_entities":
                    graph.number_of_nodes(),

                "total_relationships":
                    graph.number_of_edges()

            },

            "key_entities":
                key_entities,

            "patterns":
                patterns,

            "correlations":
                correlations,

            "investigation":
                current_investigation

        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)

        )

    finally:

        # -------------------------------------------------
        # Delete temporary file
        # -------------------------------------------------

        if temporary_file:

            try:

                if os.path.exists(
                    temporary_file
                ):

                    os.remove(
                        temporary_file
                    )

            except Exception:

                pass