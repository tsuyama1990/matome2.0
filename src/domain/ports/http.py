from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager
from typing import Any, Protocol


class IHttpResponse(Protocol):
    """Protocol for HTTP response objects."""

    def raise_for_status(self) -> Any:
        """Raises an exception for non-2xx status codes."""
        ...

    def json(self) -> Any:
        """Parses the response body as JSON."""
        ...

    def aiter_lines(self) -> AsyncIterator[str]:
        """Asynchronously yields lines from the response body."""
        ...


class IHttpClient(ABC):
    """Abstract interface for making HTTP requests."""

    @abstractmethod
    async def get(self, url: str, headers: dict[str, str], timeout: float) -> IHttpResponse:  # noqa: ASYNC109
        """Performs an asynchronous GET request.

        Raises:
            TimeoutError: If the request exceeds the timeout period.
            ConnectionError: If a network connection error occurs.
        """
        ...

    @abstractmethod
    async def post(
        self,
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,  # noqa: ASYNC109
    ) -> IHttpResponse:
        """Performs an asynchronous POST request.

        Args:
            url (str): The endpoint.
            headers (dict): Request headers.
            json (dict): JSON payload.
            timeout (float): Request timeout.

        Returns:
            IHttpResponse: A response object.

        Raises:
            TimeoutError: If the request exceeds the timeout period.
            ConnectionError: If a network connection error occurs.
        """
        ...

    @abstractmethod
    def stream_post(
        self,
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
    ) -> AbstractAsyncContextManager[IHttpResponse]:
        """Performs an asynchronous POST request and yields chunks of the response.

        This method should return an asynchronous context manager that yields a response
        object capable of asynchronously yielding lines or chunks.

        Raises:
            TimeoutError: If the request exceeds the timeout period.
            ConnectionError: If a network connection error occurs.
        """
        ...

    @abstractmethod
    async def put(
        self,
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,  # noqa: ASYNC109
    ) -> IHttpResponse:
        """Performs an asynchronous PUT request.

        Raises:
            TimeoutError: If the request exceeds the timeout period.
            ConnectionError: If a network connection error occurs.
        """
        ...

    @abstractmethod
    async def delete(self, url: str, headers: dict[str, str], timeout: float) -> IHttpResponse:  # noqa: ASYNC109
        """Performs an asynchronous DELETE request.

        Raises:
            TimeoutError: If the request exceeds the timeout period.
            ConnectionError: If a network connection error occurs.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Closes the underlying client connections."""
        ...
