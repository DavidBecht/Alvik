from asyncio import StreamWriter

from alvik_utils.utils import is_micropython

HTTP_STATUS_CODES = {
    200: "OK",
    201: "Created",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
}
class UPYStreamWriter:
    def __init__(self, writer: StreamWriter):
        self.writer = writer
        self.is_micropython = is_micropython()

    async def send_response(self, http_status_code: int, content: str, content_type:str="text/plain", connection:str="close") -> None:
        response = f"HTTP/1.1 {http_status_code} {HTTP_STATUS_CODES.get(http_status_code, 'Unknown')}\r\n"
        response += f"Content-Type: {content_type}\r\n"
        response += f"Connection: {connection}\r\n\r\n"
        response += content
        await self.awrite(response.encode("utf-8"))
        if connection == "close":
            await self.aclose()

    async def awrite(self, data: bytes) -> None:
        if self.is_micropython:
            await self.writer.awrite(data)
        else:
            self.writer.write(data)
            await self.writer.drain()

    def write(self, data: bytes):
        self.writer.write(data)

    async def aclose(self):
        if self.is_micropython:
            await self.writer.aclose()
        else:
            self.writer.close()
            await self.writer.wait_closed()