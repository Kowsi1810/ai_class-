"""
search_tool.py

Search resumes from ChromaDB.
"""

from vector_store import ResumeVectorStore
from config import TOP_K


class ResumeSearchTool:

    def __init__(self):
        """
        Initialize the search tool.
        """

        self.vector_store = ResumeVectorStore()

    def _merge_chunks_by_filename(self, docs_with_scores):
        """
        A resume is stored as several small chunks. Several chunks
        from the same resume can match a query, which would otherwise
        show up as duplicate "candidates". This groups chunks back
        together per filename (best score first, chunks in original
        order) so each candidate represents one full resume.
        """

        merged = {}

        for doc, score in docs_with_scores:

            filename = doc.metadata.get("filename", "Unknown")

            if filename not in merged:
                merged[filename] = {
                    "filename": filename,
                    "chunks": [],
                    "best_score": score,
                }

            merged[filename]["chunks"].append(
                (doc.metadata.get("page", 0), doc.page_content)
            )

            merged[filename]["best_score"] = min(
                merged[filename]["best_score"], score
            )

        candidates = []

        for filename, data in merged.items():

            ordered_chunks = [
                text for _, text in sorted(data["chunks"], key=lambda c: c[0])
            ]

            candidates.append({
                "filename": filename,
                "content": "\n".join(ordered_chunks),
                "score": data["best_score"],
            })

        # Best (lowest distance / highest similarity) resumes first
        candidates.sort(key=lambda c: c["score"])

        return candidates[:TOP_K]

    def search_resumes(self, query):
        """
        Search resumes using semantic search.

        Retrieves a wider pool of chunks, then merges chunks that
        belong to the same resume so callers get one entry per
        candidate with the full matched content.

        Parameters
        ----------
        query : str

        Returns
        -------
        list
        """

        # Pull extra chunks since several may belong to the same resume
        results = self.vector_store.similarity_search_with_score(
            query, k=TOP_K * 4
        )

        candidates = self._merge_chunks_by_filename(results)

        return [
            {"filename": c["filename"], "content": c["content"]}
            for c in candidates
        ]

    def search_with_scores(self, query):
        """
        Search resumes with similarity scores.

        Parameters
        ----------
        query : str

        Returns
        -------
        list
        """

        results = self.vector_store.similarity_search_with_score(
            query, k=TOP_K * 4
        )

        return self._merge_chunks_by_filename(results)