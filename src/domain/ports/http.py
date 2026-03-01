from abc import ABC, abstractmethod
from typing import Any


class IHttpClient(ABC):
    """Abstract interface for making HTTP requests."""

    @abstractmethod
    async def get(self, url: str, headers: dict[str, str], timeout: float) -> Any:  # noqa: ASYNC109
        """Performs an asynchronous GET request."""

    @abstractmethod
    async def post(
        self,
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,  # noqa: ASYNC109
    ) -> Any:
        """Performs an asynchronous POST request.

        Args:
            url (str): The endpoint.
            headers (dict): Request headers.
            json (dict): JSON payload.
            timeout (float): Request timeout.

        Returns:
            Any: A response object with an interface providing .raise_for_status(), .json(), and .iter_lines()
        """

    @abstractmethod
    async def put(
        self, url: str, headers: dict[str, str], json: dict[str, Any], timeout: float  # noqa: ASYNC109
    ) -> Any:
        """Performs an asynchronous PUT request."""

    @abstractmethod
    async def delete(self, url: str, headers: dict[str, str], timeout: float) -> Any:  # noqa: ASYNC109
        """Performs an asynchronous DELETE request."""

    @abstractmethod
    async def close(self) -> None:
        """Closes the underlying client connections."""
