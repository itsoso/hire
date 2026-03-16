from __future__ import annotations

from khire.clients.scholar import ScholarClient
from khire.llm import LLMClient


class ScholarAgent:
    """Analyzes academic output and extracts co-author relationships."""

    def __init__(self, scholar_client: ScholarClient | None = None, llm: LLMClient | None = None):
        self.scholar = scholar_client or ScholarClient()
        self.llm = llm or LLMClient()

    async def analyze(self, author_name: str) -> dict:
        """Analyze an author's academic profile."""
        authors = await self.scholar.search_author(author_name)
        if not authors:
            return self._empty_profile(author_name)

        # Pick the best match (highest citation count)
        author = max(authors, key=lambda a: a.get("citationCount", 0))
        author_id = author.get("authorId", "")

        papers_data = await self.scholar.get_author_papers(author_id)
        papers = [p.get("citedBy") or p for p in papers_data]  # handle nested structure

        # Extract co-authors
        co_author_counts: dict[str, int] = {}
        parsed_papers = []

        for paper_entry in papers_data:
            paper = paper_entry.get("citedBy") or paper_entry
            paper_authors = paper.get("authors", [])
            title = paper.get("title", "")
            citations = paper.get("citationCount", 0)
            venue = paper.get("venue", "")
            year = paper.get("year")

            # Find author position
            author_position = None
            for i, a in enumerate(paper_authors):
                if a.get("authorId") == author_id:
                    author_position = i
                    break

            parsed_papers.append({
                "title": title,
                "year": year,
                "citations": citations,
                "venue": venue,
                "author_position": author_position,
                "total_authors": len(paper_authors),
            })

            # Count co-authors
            for a in paper_authors:
                name = a.get("name", "")
                aid = a.get("authorId", "")
                if aid and aid != author_id and name:
                    co_author_counts[name] = co_author_counts.get(name, 0) + 1

        # Top co-authors sorted by collaboration frequency
        top_coauthors = sorted(
            [{"name": name, "papers_together": count} for name, count in co_author_counts.items()],
            key=lambda x: x["papers_together"],
            reverse=True,
        )[:10]

        total_citations = sum(p.get("citations", 0) for p in parsed_papers)

        return {
            "author_name": author_name,
            "author_id": author_id,
            "h_index": author.get("hIndex", 0),
            "total_citations": total_citations,
            "paper_count": author.get("paperCount", 0),
            "papers": sorted(parsed_papers, key=lambda p: p.get("citations", 0), reverse=True)[:20],
            "co_authors": top_coauthors,
        }

    def _empty_profile(self, name: str) -> dict:
        return {
            "author_name": name,
            "author_id": "",
            "h_index": 0,
            "total_citations": 0,
            "paper_count": 0,
            "papers": [],
            "co_authors": [],
        }
