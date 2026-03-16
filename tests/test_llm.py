import pytest
from unittest.mock import AsyncMock, patch

from khire.llm import LLMClient


@pytest.mark.asyncio
async def test_llm_client_complete():
    with patch("khire.llm.acompletion", new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value.choices = [
            type("Choice", (), {"message": type("Msg", (), {"content": "Hello from LLM"})()})()
        ]

        client = LLMClient(model="gpt-4o-mini")
        result = await client.complete("Say hello")

        assert result == "Hello from LLM"
        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args
        assert call_kwargs.kwargs["model"] == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_llm_client_complete_json():
    with patch("khire.llm.acompletion", new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value.choices = [
            type("Choice", (), {"message": type("Msg", (), {"content": '{"key": "value"}'})()})()
        ]

        client = LLMClient(model="gpt-4o-mini")
        result = await client.complete_json("Return JSON")

        assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_llm_client_switches_model():
    with patch("khire.llm.acompletion", new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value.choices = [
            type("Choice", (), {"message": type("Msg", (), {"content": "ok"})()})()
        ]

        client = LLMClient(model="claude-sonnet-4-20250514")
        await client.complete("test")

        call_kwargs = mock_completion.call_args
        assert call_kwargs.kwargs["model"] == "claude-sonnet-4-20250514"
