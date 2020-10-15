__version__ = "0.0.1"

from . import parse
from .layers import commandLeaf, hazilLayer, innerLayer, gameDataLayer, rpcLayer, spawnLayer, spawnSubcommandLayer, GetGameListV2Layer, LobbyItemLayer, UpdateGameDataLayer
from .helpers import pack, unpack, flatten

import struct
import random
import time
import math

class playerClass:
	def __init__(self, inputGameState):
		self.clientId = False
		self.playerId = -1
		
		self.color = False
		self.name = False
		self.skin = 0 
		self.hat = 0
		self.pet = 0

		
		self.alive = True
		self.infected = False
		
		self.entities = {}
		self.playerControlNetId = False # 1
		self.playerPhysicsNetId = False # 2
		self.networkTransformNetId = False # 3
		
		self.gameState = inputGameState
		
		self.gameDataEnties = []

		self.lastMoveSeq = -1 ## Tracking player movevment sequence numbers
		self.x = 0
		self.y = 0

		self.inVent = False ## Is player currently in the vents?

	def callback(self, callbackName): # Convience function to shorten callback updates
		self.gameState.callback(callbackName, {'gameState': self.gameState, 'player': self})

	def snapTo(self, ix, iy, seq):
		if seq > self.lastMoveSeq:
			x = (ix - 32767) ## Offset to center of maps
			y = (iy - 32767) ## Offset to center of maps
			self.x = x
			self.y = y

	def parseLocation(self, data):
		if len(data) == 10: ## Alive movement
			seq, ix, iy, xSpeed, ySpeed = struct.unpack("<HHHHH", data)
		if len(data) == 6: ## Ghost movement
			seq, ix, iy = struct.unpack("<HHH", data)
			xSpeed, ySpeed = 0, 0 ## Ehh, it works I guess

		if not (len(data) == 6 or len(data) == 10): ## Bad data?
			return False, False

		if seq > self.lastMoveSeq:
			x = (ix - 32767) ## Offset to center of maps
			y = (iy - 32767) ## Offset to center of maps
			
			x = (x/32767)*40 ## LERF to -40 to 40
			y = (y/32767)*40 ## LERF to -40 to 40

			self.x = x
			self.y = y
			self.lastMoveSeq = seq

			return self.x, self.y
		return False, False
	
	def vent(self, inVent):
		self.inVent = inVent

	def exiled(self):
		self.alive = False
		self.callback("Exiled")

	def murdered(self):
		self.alive = False
		self.callback("Murdered")

	def murder(self, player):
		self.callback("Murder")
		player.murdered()
			
	def setSkin(self, skinId):
		self.skin = skinId
		self.callback("SetSkin")
	
	def setHat(self, hatId):
		self.hat = hatId
		self.callback("SetHat")

	def setPet(self, petId):
		self.pet = petId
		self.callback("SetPet")

	def setColor(self, colorId):
		self.color = colorId
		self.callback("SetColor")

	def setInfected(self, isInfected):
		self.infected = isInfected
		self.callback("Infected")

	def assignId(self, playerId):
		self.playerId = playerId
		self.gameState.registerPlayerId(self, self.playerId)
		try:
			preName = self.gameState.usernameLookup[playerId]
			if not self.name:
				self.setName(preName)
		except:
			pass

	def chat(self, message):
		self.gameState.callback('Chat', {'gameState': self.gameState, 'player': self, 'message': message})

	def setUsernameFromList(self, name):
		self.setName(name)

	def setName(self, name):
		self.name = name
		self.callback("SetName")

	def addEntity(self, entity):
		try:
			self.entities[entity.netId]
			return False
		except:
			self.entities[entity.netId] = entity
			return True


class entityClass:
	def __init__(self, netId):
		self.netId = netId

	def addToPlayer(self, player):
		if player.addEntity(self):
			self.owner = player	
			return True
		return False


class gameState:
	def __init__(self, callbackDict={}):
		self.callbackDict = callbackDict ## dictionary of functions to call back to. Will not reset with game state
		self.reset()

	def callback(self, name, dataDict):
		try:
			cb = self.callbackDict[name]
		except:
			cb = False
			pass ## Callback not registered
		if cb:
			cb(dataDict)

	def gsCallback(self, name): # Convience function for game state update callbacks
		self.callback(name, {'gameState': self, 'player': None})

	def reset(self):
		self.gameId = False
		self.selfClientID = False # Holds a reference to the network id of the computer we run on
		self.hostClientID = False # The client id of the host of the game
		self.players = {}
		self.entities = {}
		self.playerIdMap = {}
		self.tick = 0
		self.sendServer = []
		self.sendClient = []
		self.storedValue = False
		self.time = 0 # Stores the current time of the engine
		self.usernameLookup = {} ## Stores a map of player id's to usernames to pass between spawn calls
		self.lastSpawnedId = False
		self.gameHasStarted = False

		self.meetingStartedBy = False ## player entity who started the last meeting
		self.meetingStartedAt = False ## Time it started at
		self.meetingReason = False ## Will be "Button" or the entity of a murdered player

		self.entityPreload = {} ## A dict of entities that had data sent to them before proper instantiation

		self.gameSettings = {}

		self.lobbyEntity = False

		self.gsCallback('Reset')

	def registerPlayerId(self, player, playerId):
		self.playerIdMap[playerId] = player
		
	def proc(self, data, ts):
		self.time = ts
		self.tick += 1
		tree = parse(data)
		nodes = []
		flatten(tree, nodes) ## Flatten the tree into the nodes
		for node in nodes: ## Process each node individually, can always traverse if needed
			self.procNode(node)

	def createPlayer(self, clientId):
		player = playerClass(self)
		player.clientId = clientId
		self.players[clientId] = player
		return player

	def removePlayer(self, clientId):
		try:
			player = self.players[clientId]
			del self.players[clientId]
		except:
			pass # Player not in player list
		try:
			if self.playerIdMap[player.playerId] == player:
				del self.playerIdMap[player.playerId]

		except:
			pass # Player id not registered

		try:
			for entity in player.entities:
				try:
					del self.entities[entity.netId]
				except:
					pass
		except:
			pass # Entity removal issue


	def addEntity( self, player, netId):
		entity = entityClass(netId)
		if entity.addToPlayer(player):
			self.entities[netId] = entity
		else:
			del entity ## Duplicates ?

	def spawnEntity(self, ownerNode, commandNode):
		if ownerNode.commandName == "Player":
			clientId = ownerNode.props["clientId"]
			try:
				player = self.players[clientId]
			except:
				## Player not yet instantiated, do so
				player = self.createPlayer(clientId)
			self.addEntity(player, commandNode.props["netId"])
		else:
			clientId = ownerNode.props["clientId"]
			if clientId == 4294967294: #Server Id
				clientId = "SERVER"
			netId = commandNode.props["netId"]
		self.lastSpawnedId = commandNode.props["netId"]


	def procNode(self, commandNode):
		if isinstance(commandNode, commandLeaf): ## Process command leafs and traverse upward for data where needed
			parentNode = commandNode.parent
			# Hazil
			if isinstance(parentNode, hazilLayer):
				if commandNode.commandName == "Hello":
					pass
			# Inner Net
			if isinstance(parentNode, innerLayer):
				if commandNode.commandName == "RemovePlayer":
					removedClientID = commandNode.props["ownerId"]
					self.removePlayer(removedClientID)

				if commandNode.commandName == "StartGame":
					self.gameHasStarted = True
					self.gsCallback('StartGame')

				if commandNode.commandName == "EndGame":
					self.gsCallback('EndGame')
					self.reset()

				if commandNode.commandName == "JoinedGame": ## Joined lobby, reset game state
					self.reset()
					self.gameId = commandNode.props["gameId"]
					self.selfClientID = commandNode.props["clientId"]
					self.hostClientID = commandNode.props["hostclientId"]
					self.gsCallback('JoinedGame')
			
			# Game Data  Layer
			if isinstance(parentNode, gameDataLayer):
				if commandNode.commandName == "Data":
					ownerId = commandNode.props["ownerId"]
					try:
						entity = self.entities[ownerId]
						player = entity.owner
					except:
						player = False
					if player:
						if ownerId == player.networkTransformNetId: ## Data addressed to player move handler!
							player.parseLocation(commandNode.props["data"])

			# RPC
			if isinstance(parentNode, rpcLayer):
				parentCommandNode = parentNode.parent.commandLeafs[parentNode]
				ownerId = parentCommandNode.props["ownerId"]
				try:
					entity = self.entities[ownerId]
					player = entity.owner
				except:
					player = False
					## Traffic sent before player spawn (ALSO OTHER UNKNOWN TRAFFIC?)


				##
				## We do not need a player for these commands
				##

				if commandNode.commandName == "SyncSettings": ## Set game settings (no player needed)
					self.gameSettings = parentNode.children[1].children[0].props
					self.gsCallback('GameSettings')

				if commandNode.commandName == "StartMeeting": ## meeting just started, players have been moved
					self.meetingStartedBy = self.entities[parentCommandNode.props["ownerId"]].owner
					self.meetingStartedAt = self.time
					self.meetingReason = "Button" ## Will be "Button" or the entity of a murdered player
					self.gsCallback('StartMeeting')

				if commandNode.commandName == "Close": ## The meeting is closing
					self.gsCallback('EndMeeting')

				if commandNode.commandName == "VotingComplete": ## Meeting voting results
					exilePlayer = False
					if commandNode.props['exiledPlayerId'] < 255:
						try:
							exilePlayer = self.playerIdMap[commandNode.props['exiledPlayerId']]
						except:
							pass # Exiled player not found
					if exilePlayer:
						exilePlayer.exiled()

				if not player: ## If we dont have a player instantiated yet
					try:
						self.entityPreload[ownerId] ## Check if we have established a preload for this entity
					except:
						self.entityPreload[ownerId] = [] ## Estalbish one if not
					self.entityPreload[ownerId].append(commandNode) ## Save command, We will rerun these commands if we see the entity spawn

				##
				## We need a player object for these commands to make sense
				##

				if player:
					if commandNode.commandName == "EnterVent":
						player.vent(True)
					if commandNode.commandName == "ExitVent":
						player.vent(False)

					if commandNode.commandName == "SnapTo":
						player.snapTo(commandNode.props["x"], commandNode.props["y"], commandNode.props["seq"])

					if commandNode.commandName == "MurderPlayer":
						murderedNetId = commandNode.props["netId"]
						murderedEntity = self.entities[murderedNetId]
						murderedPlayer = murderedEntity.owner
						player.murder(murderedPlayer) ## Do the murder

					if commandNode.commandName == "SetName":
						player.setName(commandNode.props["name"])
					if commandNode.commandName == "SetSkin":
						player.setSkin(commandNode.props['id'])
					if commandNode.commandName == "SetHat":
						player.setHat(commandNode.props['id'])
					if commandNode.commandName ==  "SetColor":
						player.setColor(commandNode.props['id'])
					if commandNode.commandName ==  "SetPet":
						player.setPet(commandNode.props['id'])
					

					if commandNode.commandName == "SetInfected":
						for playerId in commandNode.props['playerIdList']:
							self.playerIdMap[playerId].setInfected(True)

					if commandNode.commandName == "SendChat":
						message = commandNode.props["message"]
						player.chat(message)


			## Game data style player update
			if isinstance(parentNode, UpdateGameDataLayer):
				if commandNode.commandName == "Player":
					try:
						player = self.playerIdMap[commandNode.props["PlayerId"]]
					except:
						# Game data update no player
						return

					player.setName(commandNode.props["PlayerName"])
					player.setSkin(commandNode.props['SkinId'])
					player.setHat(commandNode.props['HatId'])
					player.setColor(commandNode.props['ColorId'])
					player.setPet(commandNode.props['PetId'])

			## Entity spawn
			if isinstance(parentNode, spawnLayer):
				if commandNode.commandName == "Lobby":
					if not self.lobbyEntity:
						self.lobbyEntity = parentNode.children[1].children[0].props['netId']
					else:
						pass ## Happens when we read our own fake lobby spawns
				if commandNode.commandName == "Player":
					## Player spawn
					for child in parentNode.children[1].children:
						self.spawnEntity(commandNode, child)
					## Player will exist at this point
					player = self.players[commandNode.props["clientId"]]
					playerControl, playerPhysics, networkTransform = parentNode.children[1].children
					
					## Pull out the player id from the data sent on the player control spawn
					u1, playerId = struct.unpack("BB", playerControl.props['data'])
					player.assignId(playerId)
					
					## Store the network id's of the player entities
					player.playerControlNetId = playerControl.props['netId'] ## Player control entity for the player (handles most actions)
					player.playerPhysicsNetId = playerPhysics.props['netId']  ## Handles SnapTo
					player.networkTransformNetId = networkTransform.props['netId'] ## Movement handler

					## Sometimes commands are sent to entities pre spawn. We keep these and rerun them when the spawn happens

					for netId in [player.playerControlNetId, player.playerPhysicsNetId, player.networkTransformNetId]:
						try:
							commands = self.entityPreload[netId]
							del self.entityPreload[netId] ## Remove the preload commands from the registry
						except:
							commands = []
						for rerunNode in commands:
							self.procNode(rerunNode) ## Rerun the commands sent before spawn

				if commandNode.commandName == "GameData":
					for child in parentNode.children[1].children:
						self.spawnEntity(commandNode, child)
					a1, a2 = parentNode.children[1].children # Arguments 1 and 2? (guessing at what to call it)
					self.gameDataEnties = [a1.props['netId'], a2.props['netId']]
					userCount = a1.props['data'][0]
					buffer = a1.props['data'][1:]
					for i in range(userCount):
						playerId = buffer[0]
						buffer = buffer[1:]
						slen = buffer[0]
						buffer = buffer[1:]
						userName = buffer[0:slen]
						buffer = buffer[slen:]
						u1, U2 = struct.unpack("<LH", buffer[0:6])
						buffer = buffer[6:]
						self.usernameLookup[playerId] = userName
						for clientId in self.players.keys():
							player = self.players[clientId]
							if player.playerId == playerId:
								player.setUsernameFromList(userName)
			if isinstance(parentNode, spawnSubcommandLayer):
				pass ## DO NOT HANDLE HERE!!!

	