import argparse
import base64
import json
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from scapy.all import IP, IPv6, TCP, UDP, PcapReader

from gruyere_traffic import analyze as analyze_http

HOST = "google-gruyere.appspot.com"
LIMIT = 4096
PRIVATE_HEADERS = {"cookie", "set-cookie", "authorization", "proxy-authorization"}
PRIVATE_FIELDS = {"pw", "password", "new_password", "old_password", "token"}


def analyze_saved_traffic(path, port=443):
    count = 0
    with PcapReader(path) as packets:
        for packet in packets:
            network = packet.getlayer(IP) or packet.getlayer(IPv6)
            transport = packet.getlayer(TCP) or packet.getlayer(UDP)
            if network is None or transport is None:
                continue
            if port not in (transport.sport, transport.dport):
                continue
            stamp = datetime.fromtimestamp(float(packet.time), tz=timezone.utc)
            print(f"{stamp.isoformat(timespec='milliseconds')} {transport.name} "
                  f"[{network.src}]:{transport.sport} -> [{network.dst}]:{transport.dport} "
                  f"payload={len(bytes(transport.payload))} B")
            count += 1
    print(f"Packets on port {port}: {count}")


def print_headers(message):
    for header in message.get("headers", []):
        name = header["name"]
        if name.lower() not in PRIVATE_HEADERS:
            print(f"  {name}: {header['value']}")


def analyze_har(path):
    with open(path, encoding="utf-8-sig") as source:
        entries = json.load(source)["log"]["entries"]
    count = 0
    for entry in entries:
        request = entry["request"]
        url = urlsplit(request["url"])
        if url.scheme != "https" or url.hostname != HOST:
            continue
        if url.path.rstrip("/").endswith("/login"):
            continue
        count += 1
        params = [(name, "[redacted]" if name.lower() in PRIVATE_FIELDS else value)
                  for name, value in parse_qsl(url.query, keep_blank_values=True)]
        safe_url = urlunsplit((url.scheme, HOST, url.path, urlencode(params), ""))
        print(f"\n{entry.get('startedDateTime', '')} {request['method']} {safe_url}")
        if params:
            print(f"Query parameters: {params}")
        print("Request headers:")
        print_headers(request)

        post = request.get("postData", {})
        if post:
            fields = post.get("params", [])
            if fields:
                for field in fields:
                    name = field["name"]
                    value = "[redacted]" if name.lower() in PRIVATE_FIELDS else field.get("value", field.get("fileName", ""))
                    print(f"Form field {name}: {value[:LIMIT]}")
            elif "text" in post:
                print(f"Request body preview: {post['text'][:LIMIT]}")
            else:
                print("Request body omitted by HAR export.")
        else:
            print("No request body in HAR.")

        response = entry["response"]
        print(f"Response: {response['status']} {response.get('statusText', '')}")
        print_headers(response)
        content = response.get("content", {})
        text = content.get("text")
        if text is None:
            print("Response body omitted by HAR export.")
        elif text == "":
            print("Response body is empty.")
        elif content.get("encoding") == "base64":
            preview = base64.b64decode(text[:4 * ((LIMIT + 2) // 3)])[:LIMIT]
            print(f"Response body preview (hex): {preview.hex(' ')}")
        else:
            print(f"Response body preview: {text[:LIMIT]}")
    print(f"\nGruyere requests in HAR: {count}")


def main():
    parser = argparse.ArgumentParser(description="Read captured Gruyere traffic.")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--analyze", metavar="PCAP")
    modes.add_argument("--har", metavar="HAR")
    parser.add_argument("--port", type=int, default=443,
                        help="Transport port in a network PCAP (default: 443).")
    parser.add_argument("--http-port", type=int, choices=(8008, 8080),
                        help="Read an unencrypted HTTP PCAP on this port.")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    if args.port != 443 and (not args.analyze or args.http_port):
        parser.error("--port requires --analyze without --http-port")
    if args.http_port and not args.analyze:
        parser.error("--http-port requires --analyze")
    try:
        if args.har:
            analyze_har(args.har)
        elif args.http_port:
            analyze_http(args.analyze, args.http_port)
        else:
            analyze_saved_traffic(args.analyze, args.port)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Cannot read input: {error}\n")


if __name__ == "__main__":
    main()
