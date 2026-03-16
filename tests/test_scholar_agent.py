import pytest
from unittest.mock import AsyncMock

from khire.agents.scholar_agent import ScholarAgent
from khire.clients.scholar import ScholarClient


@pytest.mark.asyncio
async def test_scholar_analyze_with_papers():
    mock_scholar = ScholarClient.__new__(ScholarClient)
    mock_scholar.search_author = AsyncMock(return_value=[
        {"authorId": "12345", "name": "Test Author", "paperCount": 50, "citationCount": 3000, "hIndex": 25}
    ])
    mock_scholar.get_author_papers = AsyncMock(return_value=[
        {
            "title": "Attention Is All You Need",
            "year": 2017,
            "citationCount": 80000,
            "venue": "NeurIPS",
            "authors": [
                {"authorId": "12345", "name": "Test Author"},
                {"authorId": "67890", "name": "Collaborator A"},
                {"authorId": "11111", "name": "Collaborator B"},
            ],
        },
        {
            "title": "BERT: Pre-training",
            "year": 2018,
            "citationCount": 50000,
            "venue": "NAACL",
            "authors": [
                {"authorId": "67890", "name": "Collaborator A"},
                {"authorId": "12345", "name": "Test Author"},
            ],
        },
    ])

    agent = ScholarAgent(scholar_client=mock_scholar)
    result = await agent.analyze("Test Author")

    assert result["author_name"] == "Test Author"
    assert result["h_index"] == 25
    assert result["total_citations"] == 130000
    assert len(result["papers"]) == 2
    assert result["papers"][0]["citations"] >= result["papers"][1]["citations"]  # sorted
    assert len(result["co_authors"]) > 0
    assert result["co_authors"][0]["name"] == "Collaborator A"  # appears in both papers
    assert result["co_authors"][0]["papers_together"] == 2


@pytest.mark.asyncio
async def test_scholar_analyze_no_results():
    mock_scholar = ScholarClient.__new__(ScholarClient)
    mock_scholar.search_author = AsyncMock(return_value=[])

    agent = ScholarAgent(scholar_client=mock_scholar)
    result = await agent.analyze("Unknown Person")

    assert result["author_name"] == "Unknown Person"
    assert result["h_index"] == 0
    assert result["papers"] == []
    assert result["co_authors"] == []


@pytest.mark.asyncio
async def test_scholar_author_position_tracking():
    mock_scholar = ScholarClient.__new__(ScholarClient)
    mock_scholar.search_author = AsyncMock(return_value=[
        {"authorId": "AAA", "name": "First Author", "paperCount": 10, "citationCount": 500, "hIndex": 8}
    ])
    mock_scholar.get_author_papers = AsyncMock(return_value=[
        {
            "title": "Paper One",
            "year": 2023,
            "citationCount": 100,
            "venue": "ICML",
            "authors": [
                {"authorId": "AAA", "name": "First Author"},
                {"authorId": "BBB", "name": "Second Author"},
            ],
        },
        {
            "title": "Paper Two",
            "year": 2024,
            "citationCount": 50,
            "venue": "NeurIPS",
            "authors": [
                {"authorId": "BBB", "name": "Second Author"},
                {"authorId": "CCC", "name": "Third Author"},
                {"authorId": "AAA", "name": "First Author"},
            ],
        },
    ])

    agent = ScholarAgent(scholar_client=mock_scholar)
    result = await agent.analyze("First Author")

    # First paper: author_position=0 (first author)
    paper1 = next(p for p in result["papers"] if p["title"] == "Paper One")
    assert paper1["author_position"] == 0

    # Second paper: author_position=2 (third in list)
    paper2 = next(p for p in result["papers"] if p["title"] == "Paper Two")
    assert paper2["author_position"] == 2
