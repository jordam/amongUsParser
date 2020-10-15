__version__ = "0.0.1"

from .layers import *
from .internal import payloadClass

def parse(data):
	payload = payloadClass(data)
	root = hazilLayer(False)
	root.parse(payload)
	return root