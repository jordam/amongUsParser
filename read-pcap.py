from amongUsParser import parse
from scapy.all import *

packets = rdpcap('pcaps\spec3.pcap')
capId = 0
for packet in packets:
	capId += 1
	if packet[IP].src[0:3] != '192': ## change as needed to tag client packets based on net
			packetSource = "server"
	else:
		packetSource = "client"
	try:
		payload = packet[UDP].payload.load
	except:
		continue
	
	layers = parse(packet[UDP].payload.load)
	print(capId, packetSource)
	try:
		layers.pprint()
	except:
		pass
	print()