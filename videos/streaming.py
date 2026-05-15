"""
HTTP Range responses for video seeking in browsers.
"""
import os
import re

from django.http import FileResponse, HttpResponse, StreamingHttpResponse


def _parse_range_header(range_header: str, file_size: int) -> tuple[int, int] | None:
    if not range_header or not range_header.startswith("bytes="):
        return None
    m = re.match(r"bytes=(\d*)-(\d*)", range_header.strip())
    if not m:
        return None
    start_s, end_s = m.group(1), m.group(2)
    if start_s == "" and end_s == "":
        return None
    if start_s == "":
        # suffix range: last N bytes
        length = int(end_s)
        if length <= 0 or length > file_size:
            return None
        return file_size - length, file_size - 1
    start = int(start_s)
    end = int(end_s) if end_s else file_size - 1
    if start < 0 or start >= file_size:
        return None
    end = min(end, file_size - 1)
    if end < start:
        return None
    return start, end


def file_streaming_response(
    file_path: str,
    request,
    content_type: str = "video/mp4",
) -> StreamingHttpResponse | HttpResponse:
    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("Range") or request.META.get("HTTP_RANGE")

    if range_header:
        parsed = _parse_range_header(range_header, file_size)
        if parsed is None:
            return HttpResponse(status=416)
        start, end = parsed
        length = end - start + 1

        def chunk_generator():
            with open(file_path, "rb") as f:
                f.seek(start)
                remaining = length
                while remaining > 0:
                    chunk_size = min(8192, remaining)
                    data = f.read(chunk_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        resp = StreamingHttpResponse(
            chunk_generator(),
            status=206,
            content_type=content_type,
        )
        resp["Content-Length"] = str(length)
        resp["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        resp["Accept-Ranges"] = "bytes"
        return resp

    return FileResponse(open(file_path, "rb"), content_type=content_type)
