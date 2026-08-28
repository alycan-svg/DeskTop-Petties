"""Custom response classes for API output."""

from fastapi.responses import JSONResponse


class UTF8JSONResponse(JSONResponse):
    """JSON response that explicitly advertises UTF-8 for Windows clients."""

    media_type = "application/json; charset=utf-8"
