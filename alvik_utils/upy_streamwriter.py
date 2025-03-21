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
        self._writer = writer
        self._is_micropython = is_micropython()
        self.keep_open = False  # in case of streams

    async def send_response(self, http_status_code: int, content: str="", content_type:str="text/plain", connection:str="close") -> None:
        response = f"HTTP/1.1 {http_status_code} {HTTP_STATUS_CODES.get(http_status_code, 'Unknown')}\r\n"
        response += f"Content-Type: {content_type}\r\n"
        response += f"Connection: {connection}\r\n\r\n"
        response += content
        await self.awrite(response.encode("utf-8"))
        if connection == "close":
            await self.aclose()

    async def awrite(self, data: bytes) -> None:
        if self._is_micropython:
            await self._writer.awrite(data)
        else:
            self._writer.write(data)
            await self._writer.drain()

    def write(self, data: bytes):
        self._writer.write(data)

    async def aclose(self):
        if self._is_micropython:
            await self._writer.aclose()
        else:
            self._writer.close()
            await self._writer.wait_closed()