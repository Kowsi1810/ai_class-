import { useState } from "react";
import { searchCandidates } from "./api.js";
import { parseRanking, parseSummary } from "./parse.js";

const PLACEHOLDER_JD = `e.g. "Looking for a frontend developer with 2+ years experience in React, HTML and CSS, comfortable working with REST APIs."`;

function initials(filename) {
  const name = filename.replace(/\.(pdf|docx?)$/i, "");
  const parts = name.split(/[\s_-]+/).filter(Boolean);
  if (parts.length === 0) return "??";
  return (parts[0][0] + (parts[1]?.[0] || "")).toUpperCase();
}

function ScoreStamp({ score }) {
  const tier = score >= 75 ? "high" : score >= 50 ? "mid" : "low";
  return (
    <div className={`stamp stamp--${tier}`} aria-label={`Match score ${score} of 100`}>
      <span className="stamp__score">{score}</span>
      <span className="stamp__of">/ 100</span>
    </div>
  );
}

function CandidateCard({ rank, candidate }) {
  const [open, setOpen] = useState(false);
  const { reason, strengths, weaknesses } = parseRanking(candidate.ranking);
  const summaryFields = parseSummary(candidate.summary);
  const nameField = summaryFields.find((f) => f.label.toLowerCase() === "name");
  const overallField = summaryFields.find((f) =>
    f.label.toLowerCase().startsWith("overall")
  );
  const otherFields = summaryFields.filter(
    (f) => f !== nameField && f !== overallField
  );

  return (
    <article className="card">
      <div className="card__tab">
        <span className="card__rank">{String(rank).padStart(2, "0")}</span>
      </div>

      <div className="card__head">
        <div className="card__avatar">{initials(candidate.filename)}</div>

        <div className="card__heading">
          <h3 className="card__name">
            {nameField ? nameField.value : candidate.filename}
          </h3>
          <p className="card__filename">{candidate.filename}</p>
        </div>

        <ScoreStamp score={candidate.match_score} />
      </div>

      {overallField && <p className="card__overall">{overallField.value}</p>}

      {otherFields.length > 0 && (
        <dl className="card__facts">
          {otherFields.map((f) => (
            <div className="card__fact" key={f.label}>
              <dt>{f.label}</dt>
              <dd>{f.value}</dd>
            </div>
          ))}
        </dl>
      )}

      <button
        type="button"
        className="card__toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        {open ? "Hide reviewer notes" : "Show reviewer notes"}
        <span className={`card__chevron ${open ? "is-open" : ""}`}>⌄</span>
      </button>

      {open && (
        <div className="card__notes">
          {reason.length > 0 && (
            <div className="notes__group">
              <h4>Why this score</h4>
              <ul>
                {reason.map((line, i) => (
                  <li key={i}>{line}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="notes__split">
            {strengths.length > 0 && (
              <div className="notes__group">
                <h4>Strengths</h4>
                <ul>
                  {strengths.map((line, i) => (
                    <li key={i}>{line}</li>
                  ))}
                </ul>
              </div>
            )}

            {weaknesses.length > 0 && (
              <div className="notes__group">
                <h4>Watch-outs</h4>
                <ul>
                  {weaknesses.map((line, i) => (
                    <li key={i}>{line}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </article>
  );
}

function EmptyState({ status }) {
  if (status === "loading") {
    return (
      <div className="empty">
        <div className="empty__mark empty__mark--spin" />
        <p>Reading resumes against the job description…</p>
      </div>
    );
  }

  if (status === "error") {
    return null;
  }

  if (status === "no-match") {
    return (
      <div className="empty">
        <div className="empty__mark">—</div>
        <p>No candidate cleared the score threshold.</p>
        <p className="empty__sub">Try lowering the minimum score, or rephrase the job description.</p>
      </div>
    );
  }

  return (
    <div className="empty">
      <div className="empty__mark">✎</div>
      <p>No search yet.</p>
      <p className="empty__sub">Describe the role on the left, and matched candidates will be listed here.</p>
    </div>
  );
}

export default function App() {
  const [jobDescription, setJobDescription] = useState("");
  const [minScore, setMinScore] = useState(50);
  const [status, setStatus] = useState("idle"); // idle | loading | done | error | no-match
  const [results, setResults] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");
  const [lastQuery, setLastQuery] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();

    if (!jobDescription.trim()) return;

    setStatus("loading");
    setErrorMessage("");

    try {
      const data = await searchCandidates(jobDescription, minScore);
      setResults(data.results);
      setLastQuery(jobDescription);
      setStatus(data.results.length === 0 ? "no-match" : "done");
    } catch (err) {
      setErrorMessage(err.message || "Something went wrong.");
      setStatus("error");
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header__mark">RA·01</div>
        <div>
          <h1>Candidate Intake</h1>
          <p className="header__sub">Resume screening, read against the role you describe</p>
        </div>
      </header>

      <main className="layout">
        <section className="panel">
          <h2 className="panel__title">Role brief</h2>

          <form onSubmit={handleSubmit} className="form">
            <label htmlFor="jd" className="form__label">
              Job description
            </label>
            <textarea
              id="jd"
              className="form__textarea"
              placeholder={PLACEHOLDER_JD}
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              rows={10}
            />

            <div className="form__row">
              <label htmlFor="minScore" className="form__label">
                Minimum match score
              </label>
              <span className="form__scoreValue">{minScore}</span>
            </div>
            <input
              id="minScore"
              type="range"
              min={0}
              max={100}
              step={5}
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="form__slider"
            />

            <button
              type="submit"
              className="form__submit"
              disabled={status === "loading" || !jobDescription.trim()}
            >
              {status === "loading" ? "Reviewing…" : "Find candidates"}
            </button>

            {status === "error" && (
              <p className="form__error">{errorMessage}</p>
            )}
          </form>
        </section>

        <section className="results">
          <div className="results__head">
            <h2 className="panel__title">
              {status === "done" || status === "no-match"
                ? `Results for “${lastQuery.slice(0, 60)}${lastQuery.length > 60 ? "…" : ""}”`
                : "Results"}
            </h2>
            {status === "done" && (
              <span className="results__count">
                {results.length} candidate{results.length === 1 ? "" : "s"} matched
              </span>
            )}
          </div>

          {status !== "done" && <EmptyState status={status} />}

          {status === "error" && (
            <div className="empty empty--error">
              <div className="empty__mark">!</div>
              <p>Couldn't reach the recruitment agent.</p>
              <p className="empty__sub">{errorMessage}</p>
            </div>
          )}

          {status === "done" && (
            <div className="results__list">
              {results.map((candidate, i) => (
                <CandidateCard
                  key={candidate.filename}
                  rank={i + 1}
                  candidate={candidate}
                />
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
