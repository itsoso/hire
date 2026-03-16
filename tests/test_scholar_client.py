import pytest
import respx
from httpx import Response

from khire.clients.scholar import ScholarClient


@respx.mock
@pytest.mark.asyncio
async def test_search_author():
    respx.get("https://api.semanticscholar.org/graph/v1/author/search").mock(
        return_value=Response(200, json={
            "data": [
                {"authorId": "123", "name": "Test Author", "paperCount": 20, "citationCount": 1000, "hIndex": 15}
            ]
        })
    )

    client = ScholarClient()
    authors = await client.search_author("Test Author")

    assert len(authors) == 1
    assert authors[0]["name"] == "Test Author"


@respx.mock
@pytest.mark.asyncio
async def test_get_author_papers():
    respx.get("https://api.semanticscholar.org/graph/v1/author/123/papers").mock(
        return_value=Response(200, json={
            "data": [
                {"title": "Paper One", "year": 2023, "citationCount": 50, "venue": "ICML", "authors": []}
            ]
        })
    )

    client = ScholarClient()
    papers = await client.get_author_papers("123")

    assert len(papers) == 1
    assert papers[0]["title"] == "Paper One"


@respx.mock
@pytest.mark.asyncio
async def test_search_author_not_found():
    respx.get("https://api.semanticscholar.org/graph/v1/author/search").mock(
        return_value=Response(200, json={"data": []})
    )

    client = ScholarClient()
    authors = await client.search_author("Nobody")

    assert authors == []
