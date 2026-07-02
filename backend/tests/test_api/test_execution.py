"""Execution API tests."""

from http import HTTPStatus
from typing import Self

import httpx
import pytest

from enums import ExecutionStatus, NodeType
from tests.factories import (
    EdgeFactory,
    ExecutionFactory,
    LLMProviderFactory,
    NodeFactory,
    WorkflowFactory,
)
from tests.test_api.base import BaseTestCase


class TestExecutionCreate(BaseTestCase):
    """Tests for POST /executions."""

    url = "/executions"

    @pytest.mark.asyncio
    async def test_ok(self) -> None:
        """Successful run creation returns finalized execution."""
        user, headers = await self.create_user_and_get_token()
        workflow = await WorkflowFactory.create_async(
            session=self.session, owner_id=user["id"]
        )
        input_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.INPUT,
            data={"label": "Input", "format": "txt"},
        )
        output_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.OUTPUT,
            data={"label": "Output", "format": "txt"},
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=input_node.id,
            target_node_id=output_node.id,
        )

        response = await self.client.post(
            url=self.url,
            json={"workflow_id": workflow.id, "input_data": {"value": "hello"}},
            headers=headers,
        )

        data = await self.assert_response_dict(response=response)
        self.assert_has_keys(
            data,
            {"id", "workflow_id", "status", "started_at", "output_data", "error"},
        )
        if data["workflow_id"] != workflow.id:
            pytest.fail("Execution workflow_id did not match request")
        if data["status"] != ExecutionStatus.SUCCESS:
            pytest.fail("Execution status did not match success state")
        if data["output_data"] != {"value": "hello"}:
            pytest.fail("Execution output did not match expected value")
        if data["error"] is not None:
            pytest.fail("Execution error should be null for success")

    @pytest.mark.asyncio
    async def test_ok_with_llm_node(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Execution succeeds with an LLM node, mocking the Ollama chat call."""

        class DummyResponse:
            """Dummy HTTP response for Ollama chat tests."""

            status_code = HTTPStatus.OK
            text = ""

            def raise_for_status(self) -> None:
                """Keep successful status."""

            def json(self) -> dict:
                """Return a mock Ollama chat payload."""
                return {
                    "model": "test-model",
                    "message": {"role": "assistant", "content": "hi from llm"},
                    "done": True,
                }

        class DummyAsyncClient:
            """Dummy async client that returns a fixed chat payload."""

            def __init__(self, *args: object, **kwargs: object) -> None:
                """Allow constructing with any httpx kwargs."""

            async def __aenter__(self) -> Self:
                """Enter async context manager."""
                return self

            async def __aexit__(
                self,
                exc_type: type[BaseException] | None,
                exc: BaseException | None,
                tb: object,
            ) -> bool:
                """Exit async context manager."""
                del exc_type, exc, tb
                return False

            async def post(self, *args: object, **kwargs: object) -> DummyResponse:
                """Return a successful chat response."""
                del args, kwargs
                return DummyResponse()

        monkeypatch.setattr("llm.ollama.httpx.AsyncClient", DummyAsyncClient)

        user, headers = await self.create_user_and_get_token()
        provider = await LLMProviderFactory.create_async(
            session=self.session,
            user_id=user["id"],
            base_url="http://ollama:11434",
        )
        workflow = await WorkflowFactory.create_async(
            session=self.session, owner_id=user["id"]
        )
        input_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.INPUT,
            data={"label": "Input", "format": "txt"},
        )
        llm_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.LLM,
            data={
                "label": "LLM",
                "llm_provider_id": provider.id,
                "model": "test-model",
                "system_prompt": "You are a helpful assistant.",
            },
        )
        output_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.OUTPUT,
            data={"label": "Output", "format": "txt"},
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=input_node.id,
            target_node_id=llm_node.id,
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=llm_node.id,
            target_node_id=output_node.id,
        )

        response = await self.client.post(
            url=self.url,
            json={"workflow_id": workflow.id, "input_data": {"value": "hello"}},
            headers=headers,
        )

        data = await self.assert_response_dict(response=response)
        if data["status"] != ExecutionStatus.SUCCESS:
            pytest.fail("Execution with LLM node should succeed")
        if data["output_data"] != {"value": "hi from llm"}:
            pytest.fail("Execution output did not match mocked LLM content")

    @pytest.mark.asyncio
    async def test_ok_with_web_search_node(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Execution succeeds with web search node in the path."""

        class DummyResponse:
            """Dummy HTTP response for web search tests."""

            status_code = HTTPStatus.OK
            text = ""

            def raise_for_status(self) -> None:
                """Keep successful status."""

            def json(self) -> dict:
                """Return mock DuckDuckGo payload."""
                return {
                    "AbstractText": "DuckDuckGo is a privacy-focused search engine.",
                    "AbstractURL": "https://duckduckgo.com/about",
                    "RelatedTopics": [
                        {
                            "Text": "DuckDuckGo Search",
                            "FirstURL": "https://duckduckgo.com",
                        }
                    ],
                }

        class DummyAsyncClient:
            """Dummy async client that returns fixed payload."""

            def __init__(self, *args: object, **kwargs: object) -> None:
                """Allow constructing with any httpx kwargs."""

            async def __aenter__(self) -> Self:
                """Enter async context manager."""
                return self

            async def __aexit__(
                self,
                exc_type: type[BaseException] | None,
                exc: BaseException | None,
                tb: object,
            ) -> bool:
                """Exit async context manager."""
                del exc_type, exc, tb
                return False

            async def get(self, *args: object, **kwargs: object) -> DummyResponse:
                """Return a successful response."""
                del args, kwargs
                return DummyResponse()

        monkeypatch.setattr("nodes.web_search.httpx.AsyncClient", DummyAsyncClient)

        user, headers = await self.create_user_and_get_token()
        workflow = await WorkflowFactory.create_async(
            session=self.session, owner_id=user["id"]
        )
        input_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.INPUT,
            data={"label": "Input", "format": "txt"},
        )
        web_search_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.WEB_SEARCH,
            data={"label": "Web Search", "max_results": 2},
        )
        output_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.OUTPUT,
            data={"label": "Output", "format": "txt"},
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=input_node.id,
            target_node_id=web_search_node.id,
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=web_search_node.id,
            target_node_id=output_node.id,
        )

        response = await self.client.post(
            url=self.url,
            json={"workflow_id": workflow.id, "input_data": {"value": "duckduckgo"}},
            headers=headers,
        )

        data = await self.assert_response_dict(response=response)
        if data["status"] != ExecutionStatus.SUCCESS:
            pytest.fail("Execution with web search node should succeed")
        output_value = (
            data.get("output_data", {}).get("value")
            if isinstance(data.get("output_data"), dict)
            else None
        )
        if not isinstance(output_value, str) or "DuckDuckGo" not in output_value:
            pytest.fail("Execution output does not contain expected web search text")

    @pytest.mark.asyncio
    async def test_web_search_runtime_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Execution is marked as failed when web search request fails."""

        class FailingAsyncClient:
            """Dummy async client that raises a timeout."""

            def __init__(self, *args: object, **kwargs: object) -> None:
                """Allow constructing with any httpx kwargs."""

            async def __aenter__(self) -> Self:
                """Enter async context manager."""
                return self

            async def __aexit__(
                self,
                exc_type: type[BaseException] | None,
                exc: BaseException | None,
                tb: object,
            ) -> bool:
                """Exit async context manager."""
                del exc_type, exc, tb
                return False

            async def get(self, *args: object, **kwargs: object) -> object:
                """Raise timeout to emulate provider failure."""
                del args, kwargs
                message = "timeout"
                raise httpx.TimeoutException(message)

        monkeypatch.setattr("nodes.web_search.httpx.AsyncClient", FailingAsyncClient)

        user, headers = await self.create_user_and_get_token()
        workflow = await WorkflowFactory.create_async(
            session=self.session, owner_id=user["id"]
        )
        input_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.INPUT,
            data={"label": "Input", "format": "txt"},
        )
        web_search_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.WEB_SEARCH,
            data={"label": "Web Search", "max_results": 3},
        )
        output_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.OUTPUT,
            data={"label": "Output", "format": "txt"},
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=input_node.id,
            target_node_id=web_search_node.id,
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=web_search_node.id,
            target_node_id=output_node.id,
        )

        response = await self.client.post(
            url=self.url,
            json={"workflow_id": workflow.id, "input_data": {"value": "duckduckgo"}},
            headers=headers,
        )

        data = await self.assert_response_dict(response=response)
        if data["status"] != ExecutionStatus.FAILED:
            pytest.fail("Expected FAILED status for web search runtime error")
        if not data.get("error"):
            pytest.fail("Expected error details for failed web search execution")

    @pytest.mark.asyncio
    async def test_input_node_count_error(self) -> None:
        """Request fails if workflow has more than one input node."""
        user, headers = await self.create_user_and_get_token()
        workflow = await WorkflowFactory.create_async(
            session=self.session, owner_id=user["id"]
        )
        first_input = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.INPUT,
            data={"label": "Input 1", "format": "txt"},
        )
        second_input = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.INPUT,
            data={"label": "Input 2", "format": "txt"},
        )
        output_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.OUTPUT,
            data={"label": "Output", "format": "txt"},
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=first_input.id,
            target_node_id=output_node.id,
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=second_input.id,
            target_node_id=output_node.id,
        )

        response = await self.client.post(
            url=self.url,
            json={"workflow_id": workflow.id, "input_data": {"value": "hello"}},
            headers=headers,
        )

        if response.status_code != HTTPStatus.BAD_REQUEST:
            pytest.fail("Expected BAD_REQUEST for invalid input node count")

    @pytest.mark.asyncio
    async def test_output_node_count_error(self) -> None:
        """Request fails if workflow has more than one output node."""
        user, headers = await self.create_user_and_get_token()
        workflow = await WorkflowFactory.create_async(
            session=self.session, owner_id=user["id"]
        )
        input_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.INPUT,
            data={"label": "Input", "format": "txt"},
        )
        first_output = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.OUTPUT,
            data={"label": "Output 1", "format": "txt"},
        )
        second_output = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.OUTPUT,
            data={"label": "Output 2", "format": "txt"},
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=input_node.id,
            target_node_id=first_output.id,
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=input_node.id,
            target_node_id=second_output.id,
        )

        response = await self.client.post(
            url=self.url,
            json={"workflow_id": workflow.id, "input_data": {"value": "hello"}},
            headers=headers,
        )

        if response.status_code != HTTPStatus.BAD_REQUEST:
            pytest.fail("Expected BAD_REQUEST for invalid output node count")

    @pytest.mark.asyncio
    async def test_cycle_error(self) -> None:
        """Request fails if workflow graph has a cycle."""
        user, headers = await self.create_user_and_get_token()
        workflow = await WorkflowFactory.create_async(
            session=self.session, owner_id=user["id"]
        )
        input_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.INPUT,
            data={"label": "Input", "format": "txt"},
        )
        llm_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.LLM,
            data={
                "label": "LLM",
                "llm_provider_id": 1,
                "model": "test-model",
                "system_prompt": "",
            },
        )
        output_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.OUTPUT,
            data={"label": "Output", "format": "txt"},
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=input_node.id,
            target_node_id=llm_node.id,
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=llm_node.id,
            target_node_id=output_node.id,
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=output_node.id,
            target_node_id=llm_node.id,
        )

        response = await self.client.post(
            url=self.url,
            json={"workflow_id": workflow.id, "input_data": {"value": "hello"}},
            headers=headers,
        )

        if response.status_code != HTTPStatus.BAD_REQUEST:
            pytest.fail("Expected BAD_REQUEST for cyclic workflow graph")

    @pytest.mark.asyncio
    async def test_invalid_input_payload(self) -> None:
        """Request fails if input payload does not match txt contract."""
        user, headers = await self.create_user_and_get_token()
        workflow = await WorkflowFactory.create_async(
            session=self.session, owner_id=user["id"]
        )
        input_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.INPUT,
            data={"label": "Input", "format": "txt"},
        )
        output_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.OUTPUT,
            data={"label": "Output", "format": "txt"},
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=input_node.id,
            target_node_id=output_node.id,
        )

        response = await self.client.post(
            url=self.url,
            json={"workflow_id": workflow.id, "input_data": {"value": 1}},
            headers=headers,
        )

        if response.status_code != HTTPStatus.UNPROCESSABLE_ENTITY:
            pytest.fail("Expected UNPROCESSABLE_ENTITY for invalid input payload")

    @pytest.mark.asyncio
    async def test_execution_runtime_error(self) -> None:
        """Runtime execution errors are persisted as failed status."""
        user, headers = await self.create_user_and_get_token()
        workflow = await WorkflowFactory.create_async(
            session=self.session, owner_id=user["id"]
        )
        input_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.INPUT,
            data={"label": "Input", "format": "txt"},
        )
        output_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.OUTPUT,
            data={"label": "Output", "format": "txt"},
        )
        llm_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.LLM,
            data={
                "label": "LLM",
                "llm_provider_id": 999999,
                "model": "test-model",
                "system_prompt": "",
            },
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=input_node.id,
            target_node_id=llm_node.id,
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=llm_node.id,
            target_node_id=output_node.id,
        )

        response = await self.client.post(
            url=self.url,
            json={"workflow_id": workflow.id, "input_data": {"value": "hello"}},
            headers=headers,
        )

        data = await self.assert_response_dict(response=response)
        if data["status"] != ExecutionStatus.FAILED:
            pytest.fail("Expected FAILED status for runtime execution error")
        if not data["error"]:
            pytest.fail("Expected error details for failed execution")

    @pytest.mark.asyncio
    async def test_execution_unexpected_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Unexpected (non-domain) errors are persisted as failed, not stranded."""

        async def _raise(*args: object, **kwargs: object) -> str:
            """Emulate an unexpected runtime failure inside a node handler."""
            del args, kwargs
            message = "boom"
            raise RuntimeError(message)

        monkeypatch.setattr("nodes.registry.NodeHandlerRegistry.execute", _raise)

        user, headers = await self.create_user_and_get_token()
        workflow = await WorkflowFactory.create_async(
            session=self.session, owner_id=user["id"]
        )
        input_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.INPUT,
            data={"label": "Input", "format": "txt"},
        )
        output_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.OUTPUT,
            data={"label": "Output", "format": "txt"},
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=input_node.id,
            target_node_id=output_node.id,
        )

        response = await self.client.post(
            url=self.url,
            json={"workflow_id": workflow.id, "input_data": {"value": "hello"}},
            headers=headers,
        )

        data = await self.assert_response_dict(response=response)
        if data["status"] != ExecutionStatus.FAILED:
            pytest.fail("Expected FAILED status for unexpected execution error")
        if data["error"] != "Internal execution error":
            pytest.fail("Expected generic error message for unexpected failure")


class TestExecutionList(BaseTestCase):
    """Tests for GET /executions."""

    url = "/executions"

    @pytest.mark.asyncio
    async def test_ok(self) -> None:
        """List returns executions for the workflow."""
        user, headers = await self.create_user_and_get_token()
        workflow = await WorkflowFactory.create_async(
            session=self.session, owner_id=user["id"]
        )

        first = await ExecutionFactory.create_async(
            session=self.session, workflow_id=workflow.id
        )
        second = await ExecutionFactory.create_async(
            session=self.session, workflow_id=workflow.id
        )

        response = await self.client.get(
            url=self.url,
            params={"workflow_id": workflow.id},
            headers=headers,
        )

        data = await self.assert_response_list(response=response)
        ids = {item.get("id") for item in data}
        if first.id not in ids or second.id not in ids:
            pytest.fail("Expected executions to appear in list")


class TestNodeExecutionList(BaseTestCase):
    """Tests for GET /executions/{execution_id}/nodes."""

    async def _create_workflow_with_input_output(self, user: dict) -> int:
        """Create a minimal input -> output workflow and return its ID."""
        workflow = await WorkflowFactory.create_async(
            session=self.session, owner_id=user["id"]
        )
        input_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.INPUT,
            data={"label": "Input", "format": "txt"},
        )
        output_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.OUTPUT,
            data={"label": "Output", "format": "txt"},
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=input_node.id,
            target_node_id=output_node.id,
        )
        return workflow.id

    @pytest.mark.asyncio
    async def test_records_node_results_on_success(self) -> None:
        """Every executed node is persisted with SUCCESS status and output."""
        user, headers = await self.create_user_and_get_token()
        workflow_id = await self._create_workflow_with_input_output(user)

        run_response = await self.client.post(
            url="/executions",
            json={"workflow_id": workflow_id, "input_data": {"value": "hello"}},
            headers=headers,
        )
        execution = await self.assert_response_dict(response=run_response)

        response = await self.client.get(
            url=f"/executions/{execution['id']}/nodes", headers=headers
        )

        data = await self.assert_response_list(response=response)
        expected_node_count = 2
        if len(data) != expected_node_count:
            pytest.fail("Expected one node execution per node in the path")
        if any(item["status"] != ExecutionStatus.SUCCESS for item in data):
            pytest.fail("Expected all node executions to be SUCCESS")
        if not any(item["output"] == "hello" for item in data):
            pytest.fail("Expected a node execution to carry the propagated output")

    @pytest.mark.asyncio
    async def test_records_failed_node(self) -> None:
        """The failing node is persisted with FAILED status and an error."""
        user, headers = await self.create_user_and_get_token()
        workflow = await WorkflowFactory.create_async(
            session=self.session, owner_id=user["id"]
        )
        input_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.INPUT,
            data={"label": "Input", "format": "txt"},
        )
        llm_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.LLM,
            data={
                "label": "LLM",
                "llm_provider_id": 999999,
                "model": "test-model",
                "system_prompt": "",
            },
        )
        output_node = await NodeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            type=NodeType.OUTPUT,
            data={"label": "Output", "format": "txt"},
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=input_node.id,
            target_node_id=llm_node.id,
        )
        await EdgeFactory.create_async(
            session=self.session,
            workflow_id=workflow.id,
            source_node_id=llm_node.id,
            target_node_id=output_node.id,
        )

        run_response = await self.client.post(
            url="/executions",
            json={"workflow_id": workflow.id, "input_data": {"value": "hello"}},
            headers=headers,
        )
        execution = await self.assert_response_dict(response=run_response)

        response = await self.client.get(
            url=f"/executions/{execution['id']}/nodes", headers=headers
        )

        data = await self.assert_response_list(response=response)
        failed = [item for item in data if item["status"] == ExecutionStatus.FAILED]
        if len(failed) != 1:
            pytest.fail("Expected exactly one FAILED node execution")
        if failed[0]["node_id"] != llm_node.id:
            pytest.fail("Expected the LLM node to be the failing node")
        if not failed[0]["error"]:
            pytest.fail("Expected error details on the failed node execution")

    @pytest.mark.asyncio
    async def test_other_user_cannot_read_node_results(self) -> None:
        """Node results of another user's execution are not accessible."""
        owner, owner_headers = await self.create_user_and_get_token()
        workflow_id = await self._create_workflow_with_input_output(owner)
        run_response = await self.client.post(
            url="/executions",
            json={"workflow_id": workflow_id, "input_data": {"value": "hello"}},
            headers=owner_headers,
        )
        execution = await self.assert_response_dict(response=run_response)

        _, other_headers = await self.create_user_and_get_token()
        response = await self.client.get(
            url=f"/executions/{execution['id']}/nodes", headers=other_headers
        )

        if response.status_code != HTTPStatus.NOT_FOUND:
            pytest.fail("Expected NOT_FOUND when reading another user's node results")
