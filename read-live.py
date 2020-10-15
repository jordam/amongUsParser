from amongUsParser.gameEngine import gameState
from scapy.all import *
import os


class interweave:
	def __init__(self, interface):
		self.game = gameState(self.callbacks())
		self.interface = interface

	def pkt_callback(self, packet):
		self.game.proc(packet[UDP].payload.load, packet.time)


	def callbacks(self):
		return {
			'Reset': self.reset_callback,
			'Chat': self.chat_callback,
			'StartMeeting': self.meeting_start_callback,
			'EndMeeting': self.meeting_ended_callback,
			'Exiled': self.exiled_callback
		}

	def reset_callback(self, ddict):
		print("game state reset")

	def chat_callback(self, ddict):
		print(ddict['player'].name, ":", ddict['message'])

	def exiled_callback(self, ddict):
		print("EXILED", ddict['player'].name)

	def meeting_start_callback(self, ddict):
		print("meeting started by", ddict['gameState'].meetingStartedBy.name)

	def meeting_ended_callback(self, ddict):
		print("meeting ended")

def pickInterface():
	if os.name == 'nt': ## windows friendly name method
		interfaces = get_windows_if_list()
		i = 0
		for interface in interfaces:
			print(i, interface['name'])
			i += 1
		return interfaces[int(input("Pick a number: "))]['name']
	else: ## non windows method
		interfaces = get_if_list()
		i = 0
		for interface in interfaces:
			print(i, interface)
			i += 1
		return interfaces[int(input("Pick a number: "))]


def main():
	interface = pickInterface()
	handler = interweave(interface)
	sniff(iface=interface, prn=handler.pkt_callback, filter="port 22023 or port 22323 or port 22123 or port 22423 or port 22523 or port 22623 or port 22723 or port 22823 or port 22923", store=0)

if __name__ == "__main__":
	main()