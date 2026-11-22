import argparse
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from scapy.all import Raw, TCP, bind_layers, conf, sniff, wrpcap
from scapy.layers.http import HTTP, HTTPRequest, HTTPResponse
from scapy.sessions import TCPSession

GRUYERE_PORT = 8008
PREVIEW_BYTES = 4096


def capture(path, seconds):
    if path.exists():
        raise SystemExit(f"Choose a new output file: {path}")
    conf.use_pcap = True
    iface = next(
        (item for item in conf.ifaces.values()
         if item.network_name.endswith("NPF_Loopback")),
        None,
    )
    if iface is None:
        raise SystemExit("Npcap loopback interface was not found.")

    def ready():
        print(f"Capture started for {seconds} seconds.", flush=True)

    packets = sniff(
        iface=iface,
        filter=f"tcp and host 127.0.0.1 and port {GRUYERE_PORT}",
        timeout=seconds,
        started_callback=ready,
    )
    if not packets:
        raise SystemExit("No packets captured.")
    with path.open("xb") as output:
        wrpcap(output, packets)
    print(f"Saved {len(packets)} packets to {path}.")


def analyze(path, port=GRUYERE_PORT):
    bind_layers(TCP, HTTP, sport=port)
    bind_layers(TCP, HTTP, dport=port)

    def show_http(packet):
        if HTTPRequest in packet:
            message = packet[HTTPRequest]
            target = message.Path.decode("utf-8", errors="replace")
            print(f"\n{message.Method.decode()} {target} {message.Http_Version.decode()}")
            query = parse_qsl(urlsplit(target).query, keep_blank_values=True)
            if query:
                print(f"Query parameters: {query}")
            start_fields = {"Method", "Path", "Http_Version"}
        elif HTTPResponse in packet:
            message = packet[HTTPResponse]
            print(f"\n{message.Http_Version.decode()} {message.Status_Code.decode()} "
                  f"{(message.Reason_Phrase or b'').decode(errors='replace')}")
            start_fields = {"Status_Code", "Reason_Phrase", "Http_Version"}
        else:
            return

        print(f"TCP ports: {packet[TCP].sport} -> {packet[TCP].dport}")
        for name, value in message.fields.items():
            if name == "Unknown_Headers":
                for header, item in value.items():
                    print(f"{header.decode(errors='replace')}: {item.decode(errors='replace')}")
            elif name not in start_fields and isinstance(value, bytes):
                print(f"{name.replace('_', '-')}: {value.decode(errors='replace')}")

        if Raw not in message:
            print("Body: (empty)")
            return
        body = message[Raw].load
        content_type = (message.Content_Type or b"").lower()
        text_body = content_type.startswith((b"text/", b"application/json",
                                              b"application/x-www-form-urlencoded",
                                              b"multipart/form-data"))
        # shortcut: UTF-8 and byte previews suit the lesson, decode by charset for other captures.
        preview = body[:PREVIEW_BYTES]
        print(f"Body ({len(body)} decoded bytes, preview up to {PREVIEW_BYTES}):")
        print(preview.decode("utf-8", errors="replace") if text_body else preview[:64].hex(" "))

    sniff(offline=str(path), session=TCPSession, prn=show_http, store=False)


def main():
    parser = argparse.ArgumentParser(description="Capture and read local Gruyere HTTP traffic.")
    commands = parser.add_subparsers(dest="mode", required=True)
    record = commands.add_parser("capture")
    record.add_argument("path", type=Path)
    record.add_argument("--seconds", type=int, choices=range(1, 601), default=120,
                        metavar="1-600")
    inspect = commands.add_parser("read")
    inspect.add_argument("path", type=Path)
    inspect.add_argument("--port", type=int, choices=(8008, 8080), default=GRUYERE_PORT)
    args = parser.parse_args()
    try:
        if args.mode == "capture":
            capture(args.path, args.seconds)
        else:
            analyze(args.path, args.port)
    except OSError as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
