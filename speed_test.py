import argparse
import sys
from http.client import HTTPException
from time import perf_counter
from urllib.parse import urlsplit
from urllib.request import urlopen


REQUEST_COUNT = 10
CHUNK_SIZE = 64 * 1024
TIMEOUT = 30


def measure_download(url: str) -> tuple[int, float]:
    downloaded_bytes = 0
    started_at = perf_counter()

    with urlopen(url, timeout=TIMEOUT) as response:
        while chunk := response.read(CHUNK_SIZE):
            downloaded_bytes += len(chunk)

        content_length = response.getheader("Content-Length")
        if content_length is not None and response.getheader("Transfer-Encoding") is None:
            if downloaded_bytes != int(content_length):
                raise OSError(
                    f"incomplete response body (expected {content_length} bytes, "
                    f"received {downloaded_bytes})"
                )

    return downloaded_bytes, perf_counter() - started_at


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure download speed over 10 requests.")
    parser.add_argument("url", help="HTTP or HTTPS URL of the resource to download")
    args = parser.parse_args()

    try:
        url = urlsplit(args.url)
    except ValueError as error:
        parser.error(str(error))
    if url.scheme not in ("http", "https") or not url.hostname:
        parser.error("url must be an absolute HTTP or HTTPS URL")

    total_bytes = 0
    total_seconds = 0.0
    for request_number in range(1, REQUEST_COUNT + 1):
        try:
            downloaded_bytes, seconds = measure_download(args.url)
        except (OSError, HTTPException, ValueError) as error:
            print(f"Request {request_number}/{REQUEST_COUNT} failed: {error}", file=sys.stderr)
            return 1
        total_bytes += downloaded_bytes
        total_seconds += seconds

    average_seconds = total_seconds / REQUEST_COUNT
    speed_mbps = total_bytes * 8 / total_seconds / 1_000_000
    print(f"Average request time: {average_seconds:.4f} s")
    print(f"Total downloaded: {total_bytes} bytes")
    print(f"Download speed: {speed_mbps:.2f} Mbps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
