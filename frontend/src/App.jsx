import { useEffect, useState } from "react";
import axios from "axios";

import { API_BASE_URL } from "./apiConfig";

import Patterns from "./Patterns";

import ReactFlow, {
  Background,
  Controls,
  MiniMap,
} from "reactflow";

import "reactflow/dist/style.css";

import { Upload } from "lucide-react";

import "./App.css";


function App() {

  // =========================
  // PAGE NAVIGATION
  // =========================

  const [activePage, setActivePage] = useState("dashboard");


  // =========================
  // BACKEND DATA
  // =========================

  const [summary, setSummary] = useState(null);

  const [keyEntities, setKeyEntities] = useState([]);

  const [network, setNetwork] = useState({
    nodes: [],
    edges: [],
  });

  const [correlations, setCorrelations] = useState({
    communication_financial: [],
    multi_source_entities: [],
  });

  const [error, setError] = useState(null);


  // =========================
  // FIR UPLOAD
  // =========================

  const [uploading, setUploading] = useState(false);


  // =========================
  // ENTITY INVESTIGATION
  // =========================

  const [selectedEntity, setSelectedEntity] = useState(null);

  const [entityEvidence, setEntityEvidence] = useState([]);


  // =========================
  // LOAD BACKEND DATA
  // =========================

  const loadDashboardData = async () => {

    try {

      const [
        summaryResponse,
        entitiesResponse,
        networkResponse,
        correlationsResponse,
      ] = await Promise.all([

        axios.get(
          `${API_BASE_URL}/api/summary`
        ),

        axios.get(
          `${API_BASE_URL}/api/key-entities`
        ),

        axios.get(
          `${API_BASE_URL}/api/network`
        ),

        axios.get(
          `${API_BASE_URL}/api/correlations`
        ),

      ]);


      setSummary(summaryResponse.data);

      setKeyEntities( entitiesResponse.data.key_entities || []);

      setNetwork(networkResponse.data);

      setCorrelations(  correlationsResponse.data.correlations || {
    communication_financial: [],
    multi_source_entities: [],
  });

      setError(null);

    } catch (err) {

      console.error(err);

      setError(
        "Unable to connect to backend"
      );

    }

  };


  useEffect(() => {

    // Schedule the asynchronous request after the effect is committed.
    // This avoids a synchronous state update during the effect itself.
    void Promise.resolve().then(loadDashboardData);

  }, []);


  // =========================
  // UPLOAD FIR
  // =========================

  const handleUploadFIR = async (event) => {

    const file = event.target.files[0];

    if (!file) {
      return;
    }


    // Check file type

    const allowedTypes = [
      "application/pdf",
      "text/plain",
    ];

    if (
      !allowedTypes.includes(file.type) &&
      !file.name.toLowerCase().endsWith(".pdf") &&
      !file.name.toLowerCase().endsWith(".txt")
    ) {

      alert(
        "Please upload a PDF or TXT FIR file."
      );

      event.target.value = "";

      return;

    }


    const formData = new FormData();

    formData.append("file", file);


    try {

      setUploading(true);

      setError(null);


      const response = await axios.post(

        `${API_BASE_URL}/api/upload-fir`,

        formData,

        {
          headers: {
            "Content-Type":
              "multipart/form-data",
          },
        }

      );


      console.log(
        "FIR Analysis:",
        response.data
      );


      // Refresh all dashboard information

      await loadDashboardData();


      // Clear previously selected entity

      setSelectedEntity(null);

      setEntityEvidence([]);


      // Return to dashboard

      setActivePage("dashboard");


      alert(
        "FIR uploaded and analyzed successfully!"
      );


    } catch (err) {

      console.error(
        "FIR upload error:",
        err
      );


      setError(
        err.response?.data?.detail ||
        "FIR processing failed."
      );


      alert(
        err.response?.data?.detail ||
        "FIR processing failed."
      );


    } finally {

      setUploading(false);

      // Allow uploading the same file again

      event.target.value = "";

    }

  };


  // =========================
  // LOAD ENTITY EVIDENCE
  // =========================

  const loadEntityEvidence = async (
    entityName
  ) => {

    try {

      const response = await axios.get(

        `${API_BASE_URL}/api/evidence/${encodeURIComponent(
          entityName
        )}`

      );


      setEntityEvidence(
        response.data.evidence
      );

    } catch (err) {

      console.error(err);

      setEntityEvidence([]);

    }

  };


  // =========================
  // ENTITY CLICK
  // =========================

  const handleEntityClick = (
    event,
    node
  ) => {

    const entity =
      keyEntities.find(
        (item) =>
          item.entity === node.id
      );


    if (!entity) {
      return;
    }


    setSelectedEntity(entity);

    loadEntityEvidence(node.id);

  };


  // =========================
  // GRAPH NODES
  // =========================

  const flowNodes = network.nodes.map(
    (node, index) => {

      const positions = {

        "Rahul Sharma": {
          x: 100,
          y: 150,
        },

        "Amit Verma": {
          x: 430,
          y: 150,
        },

        "Suresh Kumar": {
          x: 760,
          y: 150,
        },

        "UP53AB1234": {
          x: 100,
          y: 350,
        },

        "Gorakhpur Railway Station": {
          x: 430,
          y: 350,
        },

        "Location X": {
          x: 760,
          y: 350,
        },

      };


      return {

        id: node.id,

        position:
          positions[node.id] || {

            x:
              100 +
              (index % 3) * 300,

            y:
              100 +
              Math.floor(index / 3) * 200,

          },


        data: {

          label: (

            <div className="graph-node-content">

              <strong>
                {node.id}
              </strong>

              <span>
                {node.type}
              </span>

            </div>

          ),

        },


        className:
          `node-${node.type.toLowerCase()}`,

        style: {
          cursor: "pointer",
        },

      };

    }
  );


  // =========================
  // GRAPH EDGES
  // =========================

  const flowEdges = network.edges.map(
    (edge, index) => ({

      id:
        `${edge.source}-${edge.target}-${edge.relationship}-${index}`,

      source: edge.source,

      target: edge.target,

      label: edge.relationship,

      animated:
        edge.relationship === "CALLED",

      type: "smoothstep",

      data: {

        count: edge.count,

        amount: edge.amount,

      },

    })
  );


  // =========================
  // RENDER
  // =========================

  return (

    <div className="app">


      {/* =================================
          SIDEBAR
      ================================= */}

      <aside className="sidebar">


        {/* LOGO */}

        <div className="logo">
          <img src="/nyay-drishti-logo.png"
            className="nyay-logo"/>
        </div>


        {/* NAVIGATION */}

        <nav>


          {/* DASHBOARD */}

          <div

            className={`nav-item ${
              activePage === "dashboard"
                ? "active"
                : ""
            }`}

            onClick={() =>
              setActivePage("dashboard")
            }

          >

            <span>
              ◈
            </span>

            Dashboard

          </div>


          {/* NETWORK */}

          <div

            className={`nav-item ${
              activePage === "network"
                ? "active"
                : ""
            }`}

            onClick={() =>
              setActivePage("network")
            }

          >

            <span>
              ◎
            </span>

            Network

          </div>


          {/* ENTITIES */}

          <div

            className={`nav-item ${
              activePage === "entities"
                ? "active"
                : ""
            }`}

            onClick={() =>
              setActivePage("entities")
            }

          >

            <span>
              ◉
            </span>

            Entities

          </div>


          {/* PATTERNS */}

          <div

            className={`nav-item ${
              activePage === "patterns"
                ? "active"
                : ""
            }`}

            onClick={() =>
              setActivePage("patterns")
            }

          >

            <span>
              △
            </span>

            Patterns

          </div>


          {/* EVIDENCE */}

          <div

            className={`nav-item ${
              activePage === "evidence"
                ? "active"
                : ""
            }`}

            onClick={() =>
              setActivePage("evidence")
            }

          >

            <span>
              ▣
            </span>

            Evidence

          </div>


          {/* CORRELATIONS */}

          <div

            className={`nav-item ${
              activePage === "correlations"
                ? "active"
                : ""
            }`}

            onClick={() =>
              setActivePage("correlations")
            }

          >

            <span>
              ⇄
            </span>

            Correlations

          </div>


        </nav>


        {/* SIDEBAR BOTTOM */}

        <div className="sidebar-bottom">

          <div className="system-status">

            <span className="status-dot"></span>

            System Online

          </div>


          <small>
            • TEAM NYAY DRISHTI
          </small>

        </div>


      </aside>


      {/* =================================
          MAIN CONTENT
      ================================= */}

      <main className="main">


        {/* =================================
            PATTERNS PAGE
        ================================= */}

        {activePage === "patterns" && (

          <Patterns />

        )}


        {/* =================================
            NETWORK PAGE
        ================================= */}

        {activePage === "network" && (

          <div className="page">


            <div className="page-header">

              <div>

                <p className="eyebrow">
                  NETWORK INTELLIGENCE
                </p>

                <h1>
                  Network Analysis
                </h1>

                <p className="subtitle">
                  Interactive relationship graph of
                  identified entities.
                </p>

              </div>


              <span className="live-badge">
                LIVE
              </span>

            </div>


            <div className="panel network-page-panel">


              <div className="panel-header">

                <div>

                  <p className="eyebrow">
                    RELATIONSHIP GRAPH
                  </p>

                  <h2>
                    Entity Network
                  </h2>

                </div>


                <span className="live-badge">
                  {network.edges.length} CONNECTIONS
                </span>

              </div>


              <div
                className="network-graph"
                style={{
                  height: "600px",
                }}
              >

                <ReactFlow

                  nodes={flowNodes}

                  edges={flowEdges}

                  fitView

                  onNodeClick={
                    handleEntityClick
                  }

                >

                  <Background />

                  <Controls />

                  <MiniMap />

                </ReactFlow>

              </div>


            </div>


          </div>

        )}


        {/* =================================
            ENTITIES PAGE
        ================================= */}

        {activePage === "entities" && (

          <div className="page">


            <div className="page-header">

              <div>

                <p className="eyebrow">
                  INVESTIGATION
                </p>

                <h1>
                  Entities
                </h1>

                <p className="subtitle">
                  All entities identified across the
                  available intelligence sources.
                </p>

              </div>


              <span className="live-badge">
                {network.nodes.length} FOUND
              </span>

            </div>


            <div className="panel">


              <div className="panel-header">

                <div>

                  <p className="eyebrow">
                    ENTITY REGISTRY
                  </p>

                  <h2>
                    Identified Entities
                  </h2>

                </div>

              </div>


              <div className="entity-list">


                {network.nodes.map(
                  (node, index) => {

                    const entity =
                      keyEntities.find(
                        (item) =>
                          item.entity ===
                          node.id
                      );


                    return (

                      <div

                        className={`entity-item ${
                          selectedEntity?.entity ===
                          node.id
                            ? "selected"
                            : ""
                        }`}

                        key={node.id}

                        onClick={() => {

                          setSelectedEntity(
                            entity
                          );

                          loadEntityEvidence(
                            node.id
                          );

                        }}

                        style={{
                          cursor: "pointer",
                        }}

                      >


                        <div className="entity-rank">

                          {String(index + 1)
                            .padStart(2, "0")}

                        </div>


                        <div className="entity-info">

                          <strong>
                            {node.id}
                          </strong>

                          <span>
                            {node.type}
                          </span>

                        </div>


                        <div className="entity-metrics">

                          <div>

                            <small>
                              DEGREE
                            </small>

                            <strong>

                              {entity
                                ? entity.degree_centrality.toFixed(
                                    2
                                  )
                                : "0.00"}

                            </strong>

                          </div>


                          <div>

                            <small>
                              BETWEENNESS
                            </small>

                            <strong>

                              {entity
                                ? entity.betweenness_centrality.toFixed(
                                    2
                                  )
                                : "0.00"}

                            </strong>

                          </div>

                        </div>


                      </div>

                    );

                  }
                )}


              </div>


            </div>


            {/* ENTITY DETAILS */}

            {selectedEntity && (

              <section
                className="panel"
                style={{
                  marginTop: "24px",
                }}
              >

                <div className="panel-header">

                  <div>

                    <p className="eyebrow">
                      INVESTIGATION
                    </p>

                    <h2>
                      {selectedEntity.entity}
                    </h2>

                  </div>


                  <span className="live-badge">
                    {selectedEntity.type}
                  </span>

                </div>


                <div className="entity-stat-grid">

                  <div>

                    <small>
                      DEGREE CENTRALITY
                    </small>

                    <strong>
                      {selectedEntity.degree_centrality.toFixed(
                        2
                      )}
                    </strong>

                  </div>


                  <div>

                    <small>
                      BETWEENNESS CENTRALITY
                    </small>

                    <strong>
                      {selectedEntity.betweenness_centrality.toFixed(
                        2
                      )}
                    </strong>

                  </div>

                </div>


                {/* RELATIONSHIPS */}

                <div className="investigation-section">

                  <p className="section-title">
                    RELATIONSHIPS
                  </p>


                  {network.edges

                    .filter(
                      (edge) =>
                        edge.source ===
                          selectedEntity.entity ||

                        edge.target ===
                          selectedEntity.entity
                    )

                    .map(
                      (edge, index) => {

                        const otherEntity =
                          edge.source ===
                          selectedEntity.entity
                            ? edge.target
                            : edge.source;


                        let relationship =
                          edge.relationship;


                        if (edge.count) {

                          relationship +=
                            ` • ${edge.count} calls`;

                        }


                        if (edge.amount) {

                          relationship +=
                            ` • ₹${edge.amount.toLocaleString(
                              "en-IN"
                            )}`;

                        }


                        return (

                          <div
                            className="relationship-item"
                            key={index}
                          >

                            <span className="relationship-arrow">
                              →
                            </span>


                            <div>

                              <strong>
                                {otherEntity}
                              </strong>

                              <span>
                                {relationship}
                              </span>

                            </div>

                          </div>

                        );

                      }
                    )}

                </div>


                {/* EVIDENCE */}

                <div className="investigation-section">

                  <p className="section-title">
                    SUPPORTING EVIDENCE
                  </p>


                  {entityEvidence.length === 0 ? (

                    <p className="no-evidence">
                      No evidence available.
                    </p>

                  ) : (

                    entityEvidence.map(
                      (item) => (

                        <div
                          className="evidence-item"
                          key={item.record_id}
                        >

                          <div className="evidence-header">

                            <strong>
                              {item.record_id}
                            </strong>

                            <span>
                              {item.record_type}
                            </span>

                          </div>


                          <p>
                            {item.text}
                          </p>


                          <small>
                            Source: {item.source}
                          </small>

                        </div>
                      )
                    )

                  )}

                </div>


              </section>

            )}


          </div>

        )}


        {/* =================================
            EVIDENCE PAGE
        ================================= */}

        {activePage === "evidence" && (

          <div className="page">


            <div className="page-header">

              <div>

                <p className="eyebrow">
                  EVIDENCE TRACEABILITY
                </p>

                <h1>
                  Evidence
                </h1>

                <p className="subtitle">
                  Review source records supporting
                  identified entities and relationships.
                </p>

              </div>


              <span className="live-badge">
                {entityEvidence.length} RECORDS
              </span>

            </div>


            {/* ENTITY SELECTOR */}

            <div className="panel">


              <div className="panel-header">

                <div>

                  <p className="eyebrow">
                    ENTITY SELECTION
                  </p>

                  <h2>
                    Select an Entity
                  </h2>

                </div>

              </div>


              <div className="entity-list">

                {network.nodes.map(
                  (node, index) => (

                    <div

                      className={`entity-item ${
                        selectedEntity?.entity ===
                        node.id
                          ? "selected"
                          : ""
                      }`}

                      key={node.id}

                      onClick={() => {

                        const entity =
                          keyEntities.find(
                            (item) =>
                              item.entity ===
                              node.id
                          );

                        setSelectedEntity(
                          entity
                        );

                        loadEntityEvidence(
                          node.id
                        );

                      }}

                      style={{
                        cursor: "pointer",
                      }}

                    >

                      <div className="entity-rank">

                        {String(index + 1)
                          .padStart(2, "0")}

                      </div>


                      <div className="entity-info">

                        <strong>
                          {node.id}
                        </strong>

                        <span>
                          {node.type}
                        </span>

                      </div>

                    </div>

                  )
                )}

              </div>


            </div>


            {/* EVIDENCE RECORDS */}

            <div
              className="panel"
              style={{
                marginTop: "24px",
              }}
            >

              <div className="panel-header">

                <div>

                  <p className="eyebrow">
                    SOURCE RECORDS
                  </p>

                  <h2>
                    Supporting Evidence
                  </h2>

                </div>


                {selectedEntity && (

                  <span className="live-badge">
                    {selectedEntity.entity}
                  </span>

                )}

              </div>


              {!selectedEntity ? (

                <div className="no-evidence">

                  <p>
                    Select an entity to view its
                    supporting evidence.
                  </p>

                </div>

              ) : entityEvidence.length === 0 ? (

                <div className="no-evidence">

                  <p>
                    No evidence available for this entity.
                  </p>

                </div>

              ) : (

                <div>

                  {entityEvidence.map(
                    (item) => (

                      <div
                        className="evidence-item"
                        key={item.record_id}
                      >

                        <div className="evidence-header">

                          <strong>
                            {item.record_id}
                          </strong>

                          <span>
                            {item.record_type}
                          </span>

                        </div>


                        <p>
                          {item.text}
                        </p>


                        <small>
                          Source: {item.source}
                        </small>

                      </div>

                    )
                  )}

                </div>

              )}

            </div>


          </div>

        )}


        {/* =================================
            CORRELATIONS PAGE
        ================================= */}

        {activePage === "correlations" && (

          <div className="page">


            <div className="page-header">

              <div>

                <p className="eyebrow">
                  CROSS-SOURCE INTELLIGENCE
                </p>

                <h1>
                  Correlations
                </h1>

                <p className="subtitle">
                  Identify relationships that appear
                  across multiple intelligence sources.
                </p>

              </div>


              <span className="live-badge">
                ANALYSIS READY
              </span>

            </div>


            {/* COMMUNICATION + FINANCIAL */}

            <div className="panel">


              <div className="panel-header">

                <div>

                  <p className="eyebrow">
                    CROSS-SOURCE CORRELATION
                  </p>

                  <h2>
                    Communication + Financial
                  </h2>

                </div>


                <span className="live-badge">

                  {
                    correlations.communication_financial
                      .length
                  } FOUND

                </span>

              </div>


              {correlations.communication_financial
                .length === 0 ? (

                <p className="no-evidence">
                  No communication-financial correlations
                  detected.
                </p>

              ) : (

                <div className="correlation-list">

                  {correlations.communication_financial.map(
                    (item, index) => (

                      <div
                        className="correlation-card"
                        key={index}
                      >

                        <div className="correlation-header">

                          <div>

                            <span className="correlation-type">
                              COMMUNICATION ↔ FINANCIAL
                            </span>

                            <h3>
                              {item.source}
                              {" → "}
                              {item.target}
                            </h3>

                          </div>

                        </div>


                        <div className="correlation-metrics">

                          <div>

                            <small>
                              CALL ACTIVITY
                            </small>

                            <strong>
                              {item.call_count}
                            </strong>

                            <span>
                              calls
                            </span>

                          </div>


                          <div>

                            <small>
                              TRANSFER AMOUNT
                            </small>

                            <strong>
                              ₹
                              {item.amount.toLocaleString(
                                "en-IN"
                              )}
                            </strong>

                          </div>

                        </div>


                        <p className="correlation-description">
                          {item.description}
                        </p>


                      </div>

                    )
                  )}

                </div>

              )}

            </div>


            {/* MULTI-SOURCE ENTITIES */}

            <div
              className="panel"
              style={{
                marginTop: "24px",
              }}
            >

              <div className="panel-header">

                <div>

                  <p className="eyebrow">
                    SOURCE COVERAGE
                  </p>

                  <h2>
                    Multi-Source Entities
                  </h2>

                </div>


                <span className="live-badge">

                  {
                    correlations.multi_source_entities
                      .length
                  } FOUND

                </span>

              </div>


              {correlations.multi_source_entities
                .length === 0 ? (

                <p className="no-evidence">
                  No multi-source entities detected.
                </p>

              ) : (

                <div className="entity-list">

                  {correlations.multi_source_entities.map(
                    (item, index) => (

                      <div
                        className="entity-item"
                        key={item.entity}
                      >

                        <div className="entity-rank">

                          {String(index + 1)
                            .padStart(2, "0")}

                        </div>


                        <div className="entity-info">

                          <strong>
                            {item.entity}
                          </strong>

                          <span>
                            Appears across{" "}
                            {item.source_count} sources
                          </span>

                        </div>


                        <div className="source-tags">

                          {item.sources.map(
                            (source) => (

                              <span
                                className="source-tag"
                                key={source}
                              >
                                {source}
                              </span>

                            )
                          )}

                        </div>


                      </div>

                    )
                  )}

                </div>

              )}

            </div>


            {/* INVESTIGATOR NOTICE */}

            <section
              className="notice"
              style={{
                marginTop: "24px",
              }}
            >

              <div className="notice-icon">
                i
              </div>


              <div>

                <strong>
                  Cross-source analytical lead
                </strong>

                <p>
                  Correlations indicate that information
                  about an entity or relationship appears
                  across multiple data sources. These
                  correlations are analytical leads and
                  require investigator review.
                </p>

              </div>

            </section>


          </div>

        )}


        {/* =================================
            DASHBOARD PAGE
        ================================= */}

        {activePage === "dashboard" && (

          <>


            {/* HEADER */}

            <header className="header">

              <div>

                <p className="eyebrow">
                  INVESTIGATOR CONSOLE
                </p>

                <h1>
                  Network Analysis Dashboard
                </h1>

                <p className="subtitle">
                  AI-powered analysis of entities,
                  relationships and investigative evidence.
                </p>

              </div>


              <div className="header-actions">


                <label
                  className={`upload-fir-btn ${
                    uploading
                      ? "uploading"
                      : ""
                  }`}
                >

                  <Upload size={18} />

                  {uploading
                    ? "Analyzing FIR..."
                    : "Upload FIR"}


                  <input

                    type="file"

                    accept=".pdf,.txt"

                    onChange={
                      handleUploadFIR
                    }

                    disabled={uploading}

                    hidden

                  />

                </label>


                <div className="header-status">

                  <span className="status-dot"></span>

                  Backend Connected

                </div>


              </div>


            </header>


            {/* ERROR */}

            {error && (

              <div className="error">
                {error}
              </div>

            )}


            {/* STATISTICS */}

            <section className="stats-grid">


              <div className="stat-card">

                <div className="stat-label">
                  TOTAL ENTITIES
                </div>

                <div className="stat-value">

                  {summary
                    ? summary.total_entities
                    : "--"}

                </div>

                <div className="stat-description">
                  Identified entities
                </div>

              </div>


              <div className="stat-card">

                <div className="stat-label">
                  RELATIONSHIPS
                </div>

                <div className="stat-value">

                  {summary
                    ? summary.total_relationships
                    : "--"}

                </div>

                <div className="stat-description">
                  Network connections
                </div>

              </div>


              <div className="stat-card">

                <div className="stat-label">
                  DATA SOURCES
                </div>

                <div className="stat-value">
                  4
                </div>

                <div className="stat-description">
                  FIR • CDR • Financial • Surveillance
                </div>

              </div>


              <div className="stat-card">

                <div className="stat-label">
                  ANALYSIS STATUS
                </div>

                <div className="stat-value status-text">
                  READY
                </div>

                <div className="stat-description">
                  Investigation engine active
                </div>

              </div>


            </section>


            {/* DASHBOARD */}

            <section className="dashboard-grid">


              {/* NETWORK */}

              <div className="panel">


                <div className="panel-header">

                  <div>

                    <p className="eyebrow">
                      NETWORK INTELLIGENCE
                    </p>

                    <h2>
                      Investigation Overview
                    </h2>

                  </div>


                  <span className="live-badge">
                    LIVE
                  </span>

                </div>


                <div className="network-graph">

                  <ReactFlow

                    nodes={flowNodes}

                    edges={flowEdges}

                    fitView

                    attributionPosition="bottom-left"

                    onNodeClick={
                      handleEntityClick
                    }

                  >

                    <Background />

                    <Controls />

                    <MiniMap />

                  </ReactFlow>

                </div>


              </div>


              {/* KEY ENTITIES */}

              <div className="panel">


                <div className="panel-header">

                  <div>

                    <p className="eyebrow">
                      NETWORK ANALYTICS
                    </p>

                    <h2>
                      Key Entities
                    </h2>

                  </div>


                  <span className="live-badge">
                    {Array.isArray(keyEntities) ? keyEntities.length : 0} FOUND
                  </span>

                </div>


                <div className="entity-list">


                  {(Array.isArray(keyEntities) ? keyEntities : [])
                    .slice(0, 5)
                    .map(
                      (entity, index) => (

                        <div

                          className={`entity-item ${
                            selectedEntity?.entity ===
                            entity.entity
                              ? "selected"
                              : ""
                          }`}

                          key={entity.entity}

                          onClick={() => {

                            setSelectedEntity(
                              entity
                            );

                            loadEntityEvidence(
                              entity.entity
                            );

                          }}

                          style={{
                            cursor: "pointer",
                          }}

                        >

                          <div className="entity-rank">

                            {String(index + 1)
                              .padStart(2, "0")}

                          </div>


                          <div className="entity-info">

                            <strong>
                              {entity.entity}
                            </strong>

                            <span>
                              {entity.type}
                            </span>

                          </div>


                          <div className="entity-metrics">

                            <div>

                              <small>
                                DEGREE
                              </small>

                              <strong>
                                {entity.degree_centrality.toFixed(
                                  2
                                )}
                              </strong>

                            </div>


                            <div>

                              <small>
                                BETWEENNESS
                              </small>

                              <strong>
                                {entity.betweenness_centrality.toFixed(
                                  2
                                )}
                              </strong>

                            </div>

                          </div>

                        </div>

                      )
                    )}


                </div>


              </div>


            </section>


            {/* INVESTIGATOR NOTICE */}

            <section className="notice">

              <div className="notice-icon">
                i
              </div>


              <div>

                <strong>
                  Investigator decision support
                </strong>

                <p>
                  Network patterns are analytical leads
                  generated from available evidence.
                  They require human review and should not
                  be treated as automatic conclusions of
                  criminal activity.
                </p>

              </div>

            </section>


          </>

        )}


      </main>

    </div>

  );

}


export default App;