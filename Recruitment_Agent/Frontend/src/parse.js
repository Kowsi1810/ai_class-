/**
 * The backend returns ranking/summary as loosely-structured plain
 * text from an LLM (e.g. "Match Score: 80\n\nReason:\n- ...").
 * These helpers turn that into data the UI can lay out properly
 * instead of dumping a wall of text into a card.
 */

const SECTION_HEADERS = ["reason", "strengths", "weaknesses"];

export function parseRanking(text) {
  const sections = { reason: [], strengths: [], weaknesses: [] };

  if (!text) return sections;

  let current = null;

  for (const rawLine of text.split("\n")) {
    const line = rawLine.trim();
    if (!line) continue;

    const headerMatch = line.match(/^([A-Za-z]+):$/);

    if (headerMatch && SECTION_HEADERS.includes(headerMatch[1].toLowerCase())) {
      current = headerMatch[1].toLowerCase();
      continue;
    }

    if (line.toLowerCase().startsWith("match score")) continue;

    if (current) {
      const bullet = line.replace(/^[-•]\s*/, "");
      sections[current].push(bullet);
    }
  }

  return sections;
}

export function parseSummary(text) {
  const fields = [];

  if (!text) return fields;

  for (const rawLine of text.split("\n")) {
    const line = rawLine.trim();
    if (!line || line.toLowerCase() === "candidate summary") continue;

    const match = line.match(/^([A-Za-z ]+?)\s*:\s*(.+)$/);

    if (match) {
      fields.push({ label: match[1].trim(), value: match[2].trim() });
    }
  }

  return fields;
}
