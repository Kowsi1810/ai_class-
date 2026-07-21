const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

/**
 * Send a job description to the recruitment agent and get back
 * ranked, summarized candidates.
 *
 * @param {string} jobDescription
 * @param {number} minScore
 * @returns {Promise<{total_candidates: number, results: Array}>}
 */
export async function searchCandidates(jobDescription, minScore) {
  const response = await fetch(`${API_BASE}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      job_description: jobDescription,
      min_score: minScore
    })
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;

    try {
      const body = await response.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // response wasn't JSON — keep the generic message
    }

    throw new Error(detail);
  }

  return response.json();
}

export async function checkHealth() {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) throw new Error("Backend unreachable");
  return response.json();
}
