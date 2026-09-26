import { useEffect, useState } from "react";
import axios from "axios";
import API_BASE_URL from "./apiConfig";

function Patterns() {
  const [patterns, setPatterns] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios
      .get(`${API_BASE_URL}/api/patterns`)
      .then((response) => {
        setPatterns(response.data.patterns || {});
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError("Unable to load investigation patterns");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="page">
        <p className="eyebrow">INVESTIGATION</p>
        <h1>Suspicious Patterns</h1>
        <p className="subtitle">Analyzing network activity...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="error">{error}</div>
      </div>
    );
  }

  const sections = [
    {
      key: "high_connectivity",
      title: "High Connectivity",
      description:
        "Entities with a high number of connections in the analyzed network.",
    },
    {
      key: "network_bridges",
      title: "Network Bridges",
      description:
        "Entities connecting different parts of the network.",
    },
    {
      key: "high_call_activity",
      title: "High Call Activity",
      description:
        "Communication relationships with unusually high call activity.",
    },
    {
      key: "large_transactions",
      title: "Large Transactions",
      description:
        "Financial relationships involving significant transaction amounts.",
    },
  ];

  return (
    <div className="page">

      <div className="page-header">
        <div>
          <p className="eyebrow">INVESTIGATIVE SIGNALS</p>

          <h1>Suspicious Patterns</h1>

          <p className="subtitle">
            Analytical patterns detected from available network evidence.
          </p>
        </div>

        <span className="live-badge">
          ANALYSIS COMPLETE
        </span>
      </div>


      <div className="pattern-grid">

        {sections.map((section) => {

          const items = patterns?.[section.key] || [];

          return (
            <div className="pattern-card" key={section.key}>

              <div className="pattern-card-header">

                <div>
                  <p className="eyebrow">
                    SIGNAL
                  </p>

                  <h2>
                    {section.title}
                  </h2>
                </div>

                <span className="pattern-count">
                  {items.length}
                </span>

              </div>


              <p className="pattern-description">
                {section.description}
              </p>


              <div className="pattern-list">

                {items.length === 0 ? (

                  <div className="empty-pattern">
                    No patterns detected.
                  </div>

                ) : (

                  items.map((item, index) => (

                    <div
                      className="pattern-item"
                      key={index}
                    >

                      <div className="pattern-number">
                        {String(index + 1).padStart(2, "0")}
                      </div>


                      <div className="pattern-content">

                        <strong>
                          {item.entity ||
                            `${item.source} → ${item.target}`}
                        </strong>


                        <p>
                          {item.description}
                        </p>


                        <div className="pattern-meta">

                          {item.score !== undefined && (
                            <span>
                              Score: {item.score.toFixed(2)}
                            </span>
                          )}

                          {item.count !== undefined && (
                            <span>
                              Calls: {item.count}
                            </span>
                          )}

                          {item.amount !== undefined && (
                            <span>
                              Amount: ₹{item.amount.toLocaleString()}
                            </span>
                          )}

                          {item.record_id && (
                            <span>
                              Evidence: {item.record_id}
                            </span>
                          )}

                        </div>

                      </div>

                    </div>

                  ))

                )}

              </div>

            </div>
          );
        })}

      </div>


      <section className="notice">

        <div className="notice-icon">
          i
        </div>

        <div>

          <strong>
            Investigator decision support
          </strong>

          <p>
            Detected patterns represent analytical signals from
            available evidence. They require investigator review
            and should not be treated as automatic conclusions
            of criminal activity.
          </p>

        </div>

      </section>

    </div>
  );
}

export default Patterns;