from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware


class ContentTypeValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.headers.get("Content-Type") == "plain/text":
            raise HTTPException(status_code=400, detail="Invalid Content-Type")
        response = await call_next(request)
        return response
