import struct
from .helpers import pack, unpack, invert
from .internal import payloadClass

class layerBase:
	def __init__(self, parent):
		self.settings()
		#self.name
		#self.pullCommandByte
		#self.fieldBeforeSize
		#self.sizeField
		#self.order
		self.fieldBeforeSizeData = False

		self.initMap()
		#self.map

		self.props = {}
		self.errorFlag = False
		self.children = []
		self.commandLeafs = {} ## Reference indicating the command leaf belonging to the subcommand. Pass layer object to recieve command leaf for object
		self.parent = self.parentChildLink(parent)
		self.layer = self.locateLayer()
		
		
		self.commandName = "Root"
		self.extranious = False
	
	def parse(self, payload):
		payload.resetCounter()

		try:
			while payload.len():
				childHandler, childPayload, props, extranious, currentCommandId, currentCommandName = self._process(payload)

				commandChild = commandLeaf(self)
				commandChild.props = props
				commandChild.extranious = extranious
				commandChild.commandName = currentCommandName

				self.commandLeafs[self] = commandChild
				

				if childHandler:
					child = childHandler(self)
					child.parse(childPayload)
					self.commandLeafs[child] = commandChild
		except:
			self.handleError()
			print("LAYER ERROR", self.name)

	def structUnpack(self, structure, myPayload):
		output = []
		if structure != False:
			structSegments = structure.split('|') # Strings are processed special
			needString = False
			# Go through each segment in the split struct
			for structDef in structSegments:
				if len(structDef):
					nStructDef = structDef[0]
				else:
					nStructDef = ''
				if nStructDef in ['s', 'P', 'p', '?', 'X']: ## added special data types
					if nStructDef == 's': # Variable length string
						stringLength = myPayload.get(1)[0]
						value = myPayload.get(stringLength)

					if nStructDef == 'P': # array of packed data
						unpackCount = struct.unpack("<B", myPayload.get(1))[0]
						values = []
						## Hack to support not knowing how many bytes we consume
						pval = myPayload.value
						for x in range(unpackCount):
							value, pval = unpack(pval)
							values.append(value)
						value = values
						took = len(myPayload.value) - len(pval)
						discard = myPayload.get(took)
						## End hack

					if nStructDef == 'p': # Single packed value
						pval = myPayload.value
						value, pval = unpack(pval)
						took = len(myPayload.value) - len(pval)
						discard = myPayload.get(took)

					if nStructDef == '?': # Unknown, grab extra
						value = myPayload.get(myPayload.len())

					if nStructDef == 'X': # Pack data before size field into here if applicable
						value = self.fieldBeforeSizeData

					output.append(value)
					structDef = structDef[1:]

				if len(structDef):
					output += list(struct.unpack(self.order+structDef, myPayload.get(struct.Struct(self.order+structDef).size)))
		return output


	def _process(self, incomingPayload):
		## Check if we need to pull data before a size field for some forsaken reason... stares
		if self.fieldBeforeSize:
			self.fieldBeforeSizeData = self.structUnpack(self.fieldBeforeSize, incomingPayload)[0] ## Saved for |X struct parser

		## Get size if needed
		if self.sizeField:
			size = struct.unpack(self.sizeField, incomingPayload.get(struct.Struct(self.sizeField).size))[0]
			#print(self.name, "SIZE", size)
			myPayload = payloadClass(incomingPayload.get(size+1))
		else:
			size = 0
			myPayload = incomingPayload

		if self.pullCommandByte:
			currentCommandId = myPayload.get(1)[0]
		else:
			currentCommandId = 0 ## Default to 0

		## Check if command exists, handle if not
		try:
			currentCommandName = self.map[currentCommandId]
		except:
			self.handleError()
			## Handle the error state internally as well
			currentCommandName = "UNKNOWN! (Command Not Found) [" + str(currentCommandId) + "]"
			extranious = myPayload.get(myPayload.len())
			props = {}
			childHandler = False
			childPayload = False
			return childHandler, childPayload, props, extranious, currentCommandId, currentCommandName

		## Get command structure
		commandId, structure, argNames, childHandler = self.commands()[currentCommandName]

		## Parse out the data using the structure and argument names provided
		props, extranious, childPayload = self._handlePayload(myPayload, structure, argNames, childHandler)

		return childHandler, childPayload, props, extranious, currentCommandId, currentCommandName
		
		
	def _handlePayload(self, myPayload, structure, argNames, childHandler):
		output = {}
		extranious = None

		results = self.structUnpack(structure, myPayload)
		argOn = 0
		for item in results:
			output[argNames[argOn]] = item
			argOn += 1

		if not childHandler and myPayload.len():
			extranious = myPayload.get(myPayload.len())

		return output, extranious, myPayload

	def addChild(self, child):
		self.children.append(child)
				
	def locateLayer(self):
		layer = 0
		parentTest = self.parent
		while parentTest:
			parentTest = parentTest.parent
			layer += 1
		return layer
	
	def initMap(self):
		if self.commands():
			self.map = invert(self.commands())
		else:
			self.map = False

	def parentChildLink(self, parent):
		if parent:
			parent.addChild(self)
			return parent
		return None

	def pprint(self):
		errorStr = ""
		if self.errorFlag:
			errorStr = " : ERROR"
		print(self.t(0) + self.name + errorStr)
		if not len(self.children):
			print( self.t(1), self.commandName) 
		for propName in self.props.keys():
			print( self.t(2), propName, ":", self.props[propName] )
		if self.extranious:
			print( self.t(3), "(e):", self.extraniousPrintable() )
		for child in self.children:
			child.pprint()
		
	def extraniousPrintable(self):
		if self.extranious:
			return ":".join(["{:02x}".format(x) for x in self.extranious])
		else:
			return ""

	def t(self, extra):
		return ('\t'*self.layer) + ('-'*extra)
	

	def handleError(self):
		self.errorFlag = 1;
		#die() ## switch on to pull out errors

class commandLeaf(layerBase):
	def settings(self):
		self.name = "Command Leaf"
		self.pullCommandByte = False
		self.fieldBeforeSize = False
		self.sizeField = False
		self.order = False
	def commands(self):
		return False