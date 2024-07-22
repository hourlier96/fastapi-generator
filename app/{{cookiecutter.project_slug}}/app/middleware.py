import inspect
import json
import time
from collections.abc import AsyncIterator
from typing import Any

from fastapi import FastAPI
from pydantic import ValidationError
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.types import Message
from starlette_context import context

from app.core.cloud_logging import log, logger_struct
from app.core.config import settings


class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> StreamingResponse:
        try:
            if inspect.iscoroutinefunction(call_next):
                response = await call_next(request)
            else:
                response = call_next(request)  # type: ignore
        except ValidationError as e:
            log.warning(e)
            response = JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": e.errors()}
            )
        except ValueError as e:
            log.warning(e)
            response = JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": [{"msg": str(e), "loc": request.url.path, "type": "Value error"}]
                },
            )
        except Exception as e:
            log.warning(e)
            status_ = getattr(e, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
            response = JSONResponse(
                status_code=status_,
                content={"detail": [{"msg": str(e), "loc": request.url.path, "type": "Unknown"}]},
            )
        return response  # type: ignore


class LoggingMiddlewareReq(BaseHTTPMiddleware):
    """
    Get the body request and the body response, and all the information about the request
    It will log all the information about the request and the response
    """

    def __init__(self, app: FastAPI):
        super().__init__(app)

    async def set_body(self, request: Request, body: bytes) -> None:
        """Issue with starlette : https://github.com/encode/starlette/issues/847
        Need to override the receive method to get the body of the request, otherwise it will hang
        """

        async def receive() -> Message:
            return {"type": "http.request", "body": body}

        request._receive = receive

    async def get_body(self, request: Request) -> bytes:
        """Workaround for hang issue"""
        body = await request.body()
        await self.set_body(request, body)
        return body

    async def read_bytes(self, generator: AsyncIterator[bytes]) -> bytes:
        body = b""
        async for data in generator:
            body += data
        return body

    async def resolve_response(self, streaming_response: Any) -> Response:
        """Resolve the response from the streaming response"""
        content = await self.read_bytes(streaming_response.body_iterator)
        status_code = streaming_response.status_code
        headers = dict(streaming_response.headers) if streaming_response.headers else None
        media_type = "application/json"
        background = streaming_response.background
        return Response(content, status_code, headers, media_type, background)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Any:
        try:
            request_body = None
            try:
                request_body = json.loads(await request.body())
            except Exception:
                pass
            response = await call_next(request)
            response_body = await self.resolve_response(response)
            if settings.ENV in ["local", "test"]:
                self._log_request(request, request_body, context)
                self._log_response(request, response_body)
            logger_struct.log_struct(
                {
                    "user": context.get("USER_ID"),
                    "method": request.method,
                    "path": request.url.path,
                    "path_params": request.path_params,
                    "query": request.query_params._dict,
                    "body": request_body if request_body else {},
                    "status_code": response_body.status_code,
                    "content": response_body.body.decode("utf-8"),
                }
            )
        except Exception as e:
            log.error("Error in logging middleware")
            log.error(e)
        finally:
            return response_body if response_body else response

    def _log_request(self, request, request_body, context):
        log_lines = [f"===== REQUEST ({request.method} {request.url.path}) ====="]

        log_lines.append("    Author:")
        log_lines.append(f"        {context.get('USER_ID', 'Unknown')}")

        for param_type, params in [
            ("Query parameters:", request.query_params._dict),
            ("Path parameters:", request.path_params),
            ("Body:", request_body),
        ]:
            log_lines.append(f"    {param_type}")
            if params:
                log_lines.extend(f"        {key}: {value}" for key, value in params.items())
            else:
                log_lines.append("        Empty")

        print("\n".join(log_lines))

    def _log_response(self, request, response_body):
        header = f"\n===== RESPONSE ({request.method} {request.url.path}) =====\n"

        if response_body:
            content = json.loads(response_body.body.decode("utf-8"))
            status_code = f"    Status code:\n        {response_body.status_code}"
            content_length = f"\n    Content-Length:\n        {len(str(content))}"
            content_summary = (
                f"        {content['total']} items"
                if content and "total" in content
                else (
                    f"        {len(content)} items"
                    if isinstance(content, list)
                    else f"        {content}"
                )
            )
        else:
            status_code = "    Status code: (Unknown)"
            content_length = "\n    Content-Length: (Unknown)"
            content_summary = "\n    Content: (Unknown)"

        log_message = (
            f"{header}"
            f"{status_code}"
            f"{content_length}"
            f"\n    Content:\n{content_summary}\n"
            f"{''.join(['=' for _ in header])[:100]}\n"
        )

        print(log_message)


class MetricMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> StreamingResponse:
        start = time.perf_counter()
        if inspect.iscoroutinefunction(call_next):
            response = await call_next(request)
        else:
            response = call_next(request)  # type: ignore
        end_time = time.perf_counter() - start
        log.info(f"Request time {end_time:.3f} seconds")
        response.headers["X-Request-Time"] = f"{end_time:.3f}"
        return response  # type: ignore
