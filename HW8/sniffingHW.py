from scapy.all import conf, sniff, wrpcap
from ipaddress import ip_address
conf.use_pcap = True
conf.ifaces.show()
iface = conf.ifaces.dev_from_index(int(9))
server_ip = ip_address("64.233.165.153")
capture_filter = f"host {server_ip}"
packets = sniff(iface=iface, filter=capture_filter, timeout=30, started_callback=lambda: print("Capture started", flush=True))
len(packets)
packets[:10].summary()
if packets:
    with open("withXSS.pcap", "xb") as output:
        wrpcap(output, packets)