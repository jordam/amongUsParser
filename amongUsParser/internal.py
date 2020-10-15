class payloadClass:
	def __init__(self, value):
		self.value = value
		self.original = value
		self.counter = 0
	def len(self):
		return len(self.value)
	def get(self, count):
		self.counter += count
		output = self.value[:count]
		self.value = self.value[count:]
		return output
	def resetCounter(self):
		self.counter = 0