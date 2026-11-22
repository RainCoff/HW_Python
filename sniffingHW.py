from scapy.all import conf, sniff, wrpcap
from ipaddress import ip_address
conf.use_pcap = True
conf.ifaces.show()
iface = conf.ifaces.dev_from_index(int(9))
server_ip = ip_address("173.194.222.153")
capture_filter = f"host {server_ip} and (tcp port 443 or udp port 443)"
packets = sniff(iface=iface, filter=capture_filter, timeout=30, started_callback=lambda: print("Capture started", flush=True))
len(packets)
packets[:10].summary()
if packets:
    with open("gruyere-online.pcap", "xb") as output:
        wrpcap(output, packets)