from .baseClasses import layerBase, commandLeaf

# Layer definition file 
#
# Layers are created as a child of layerBase which contains the logic
# commands denotes the layer commands, data structure, variable names, and inheritence
# settings denotes some meta data / settings about how to processs that layer
#
# Data flows in through the top layer and down into children layers with data and information being parsed off from the data stream as it goes


# commands() structure
# Dict of lists
#	Key is commandName
#	Outer list is (command Id, argument structure, argument list, child handler)
#	Argument list is just a list of names to call obtained values
#	A child hander denotes where to send the remaining payload data once processed on the current layer
#		False will indicate no child, and extranious data from that layer will be stored not passed
#	A parent with a child handler will continue to spawn children and pass data to them until all data is consumed
#		This allows for an array of childen on some layers

# Had to add optional fromServer parameter to commands.
# Defaulting to none on classes that do not utilize it
# Currently only needed for GetGameListV2 


# Settings info
# name is the printable name of the layer
# pullCommandByte denotes if we have to pull a command byte on this layer. No defaults to command 0
# sizeField is if we have a field denoting a the size of the payload to pass to the next handler
# fieldBeforeSize denotes we have a field before the sizeField, and the data type if so
#	It is assumed the byte order is the same as the current layer
#	The value can be referred to and set via the |X special struct denotation
#		This allows you to assign an argument name


# Structure info
# Base format is https://docs.python.org/3/library/struct.html
# Special escape charecter | was added, it denotes the next charecter is a special structure not in the python defaults
#
# Structure Additions:
#
#	|s	Variable length string, 1 byte for string length followed by that amount of bytes of data
#
#	|p	Single packed value, variable length, unpacked using unpack algorithem from hazil networking.
#			Pack/Unpack attempts to save bytes by replacing one bit from each byte as a stop bit 
#			Stop bit indicates end of data. No way to tell size without attempting unpack
#			RFC6256
#
#	|P	Arry of packed values. 1 byte for count of packed values followed by values. Variable length data.
#
#	|X	Placeholder to insert data obtained from fieldBeforeSize, 0 bytes consumed here
#			Used to give the fieldBeforeSize data a name
#
#	|?	Unknown / Debug. Consumes all remaining payload data on that level into a byte string
#			Payload data is limited by size fields and nested layers. Wont usualy overrun boundaries
#


class hazilLayer(layerBase):
	def commands(self):
		return {
			'UnreliableData': [0, '', [], innerLayer],
			'ReliableData': [1, 'H', ['seq'], innerLayer],
			'Hello': [8, 'HHHB|s', ["U1", "U2", "U3", "U4", "name"], False], #STUB
			'Disconnect': [9, '', [], False],
			'Ack': [10, 'HB', ['seq', 'flag'], False],
			'Frag': [11, False, [], False], # Unused? Removed?
			'Ping': [12, 'H', ['seq'], False],
		}
	def settings(self):
		self.name = "Hazil"
		self.pullCommandByte = True
		self.fieldBeforeSize = False
		self.sizeField = False
		self.order = ">"

class innerLayer(layerBase):
	def commands(self):
		return {
			'HostGame': [0, False, [], False],
			'JoinGame': [1, 'L|?', ['gameId', 'U1'], False],
			'StartGame': [2, 'L', ['gameId'], False],
			'RemoveGame': [3, False, [], False],
			'RemovePlayer': [4, 'LLLB', ['gameId', 'ownerId', 'hostId', 'Reason'], False],
			'GameData': [5, 'L', ['gameId'], gameDataLayer],
			'GameDataTo': [6, 'L|p', ['gameId', 'clientId'], gameDataLayer],
			'JoinedGame': [7, 'LLL|P', ['gameId', 'clientId', 'hostclientId', 'otherclientIdssPacked'], False],
			'EndGame': [8, 'LH', ['gameId', 'reason?'], False], # Unsure
			'GetGameList': [9, False, [], False],
			'AlterGame': [10, 'BB', ['U1', 'U2'], False],
			'KickPlayer': [11, 'L|pB', ['gameId', 'clientId', 'banFlag?'], False],
			'WaitForHost': [12, False, [], False],
			'Redirect': [13, False, [], False],
			'RedirectServer': [14, False, [], False],
			'GetGameListV2': [16, '', [], GetGameListV2Layer],
		}
	def settings(self):
		self.name = 'InnerNet'
		self.pullCommandByte = True
		self.fieldBeforeSize = False
		self.sizeField = "<H"
		self.order = '<'


class gameDataLayer(layerBase):
	def commands(self):
		return {
			'Data': [1, '|p|?' , ['ownerId', 'data'], False], ## Data must be handled by state aware entities
			'RpcCall': [2, '|p', ['ownerId'], rpcLayer],
			'Spawn': [4, '', [], spawnLayer],
			'Despawn': [5, '|p', ['netId'], False],
			'SceneChange': [6, '|p|s', ['clientId', 'sceneName'], False],
			'Ready': [7, False, [], False],
			'ChangeSettings': [8, False, [], False],
		}
	def settings(self):
		self.name = 'GameData'
		self.pullCommandByte = True
		self.fieldBeforeSize = False
		self.sizeField = "<H"
		self.order = '<'


class rpcLayer(layerBase):
	def commands(self):
		return {
			'PlayAnimation': [0, 'B', ['id'], False],
			'CompleteTask': [1, '|p', ['id'], False],
			'SyncSettings': [2, '', [], gameSettingsLayer],
			'SetInfected': [3, '|P', ['playerIdList'], False], ## list of bytes not technically packed. should work though 
			'Exiled': [4, False, [], False],
			'CheckName': [5, False, [], False],
			'SetName': [6, '|s', ['name'], False],
			'CheckColor': [7, False, [], False],
			'SetColor': [8, 'B', ['id'], False],
			'SetHat': [9, 'B', ['id'], False],
			'SetSkin': [10, 'B', ['id'], False],
			'ReportDeadBody': [11, 'B', ['playerId'], False],
			'MurderPlayer': [12, '|p', ['netId'], False],
			'SendChat': [13, 's', ['message'], False],
			'StartMeeting': [14, 'B', ['playerId'], False],
			'SetScanner': [15, False, [], False],
			'SendChatNote': [16, False, [], False],
			'SetPet': [17, 'B', ['id'], False],
			'SetStartCounter': [18, False, [], False],
			'EnterVent': [19, 'B', ['ventId'], False],
			'ExitVent': [20, 'B', ['ventId'], False],
			'SnapTo': [21, 'HHH', ['x', 'y', 'seq'], False],
			'Close': [22, '', [], False],
			'VotingComplete': [23, '|sBB', ['states', 'exiledPlayerId', 'tie'], False],
			'CastVote': [24, False, [], False],
			'ClearVote': [25, False, [], False],
			'AddVote': [26, False, [], False],
			'CloseDoorsOfType': [27, 'B', ['type'], False],
			'RepairSystem': [28, False, [], False],
			'SetTasks': [29, False, [], False],
			'UpdateGameData': [30, '', [], UpdateGameDataLayer],
		}
	def settings(self):
		self.name = 'RPC'
		self.pullCommandByte = True
		self.fieldBeforeSize = False
		self.sizeField = False
		self.order = '<'

class UpdateGameDataLayer(layerBase):
	def commands(self):
		return {
			'Player': [0, 'B|sBBBBB|P', ['PlayerId', 'PlayerName', 'ColorId', 'HatId', 'PetId', 'SkinId', 'Flags', 'Tasks'], False]
		}
			
	def settings(self):
		self.name = 'UpdateGameData'
		self.pullCommandByte = False
		self.fieldBeforeSize = False
		self.sizeField = "<H"
		self.order = '<'

class GetGameListV2Layer(layerBase):
	def commands(self):
		return {
			'LobbyList': [0, '', [], LobbyItemLayer],
			'RequestList': [2, 'BLBffffBBBlBBLLBB', ['MaxPlayers', 'Keywords', 'MapId', 'PlayerSpeedMod', 'CrewLightMod', 'ImpostorLightMod', 'KillCooldown', 'NumCommonTasks', 'NumLongTasks', 'NumShortTasks', 'NumEmergencyMeetings', 'NumImpostors', 'KillDistance', 'DiscussionTime', 'VotingTime', 'IsDefaults', 'EmergencyCooldown'], False]
		}

	def settings(self):
		self.name = 'GameListV2'
		self.pullCommandByte = True
		self.fieldBeforeSize = False
		self.sizeField = "<H"
		self.order = '<'


class LobbyItemLayer(layerBase):
	def commands(self):
		return {
			'Lobby': [0, 'LHL|sB|pBBB' , ['IpAddress', 'Port', 'gameId', 'Name', 'Players', 'Age', 'MapId', 'Impostors', 'MaxPlayers'], False]
		}
	def settings(self):
		self.name = 'LobbyItem'
		self.pullCommandByte = True
		self.fieldBeforeSize = False
		self.sizeField = "<H"
		self.order = '<'

class gameSettingsLayer(layerBase):
	def commands(self):
		return {
			'v1': [1, 'BLBffffBBBlBBLLB', ['MaxPlayers', 'Keywords', 'MapId', 'PlayerSpeedMod', 'CrewLightMod', 'ImpostorLightMod', 'KillCooldown', 'NumCommonTasks', 'NumLongTasks', 'NumShortTasks', 'NumEmergencyMeetings', 'NumImpostors', 'KillDistance', 'DiscussionTime', 'VotingTime', 'IsDefaults'], False],
			'v2': [2, 'BLBffffBBBlBBLLBB', ['MaxPlayers', 'Keywords', 'MapId', 'PlayerSpeedMod', 'CrewLightMod', 'ImpostorLightMod', 'KillCooldown', 'NumCommonTasks', 'NumLongTasks', 'NumShortTasks', 'NumEmergencyMeetings', 'NumImpostors', 'KillDistance', 'DiscussionTime', 'VotingTime', 'IsDefaults', 'EmergencyCooldown'], False],
			'v3': [3, 'BLBffffBBBlBBLLBBBB', ['MaxPlayers', 'Keywords', 'MapId', 'PlayerSpeedMod', 'CrewLightMod', 'ImpostorLightMod', 'KillCooldown', 'NumCommonTasks', 'NumLongTasks', 'NumShortTasks', 'NumEmergencyMeetings', 'NumImpostors', 'KillDistance', 'DiscussionTime', 'VotingTime', 'IsDefaults', 'EmergencyCooldown', 'ConfirmImpostor', 'VisualTasks'], False]
		}

	def settings(self):
		self.name = 'GameSettings'
		self.pullCommandByte = True
		self.fieldBeforeSize = False
		self.sizeField = "<B"
		self.order = '<'


class spawnLayer(layerBase):
	def commands(self):
		return {
			'ShipStatus': [0, '|pBB', ['clientId', 'U1', 'spawnCount'], spawnSubcommandLayer],
			'MeetingHud': [1, '|pBB', ['clientId', 'U1', 'spawnCount'], spawnSubcommandLayer],
			'Lobby': [2, '|pBB', ['clientId', 'U1', 'spawnCount'], spawnSubcommandLayer],
			'GameData': [3, '|pBB', ['clientId', 'U1', 'spawnCount'], spawnSubcommandLayer],
			'Player': [4, '|pBB', ['clientId', 'U1', 'spawnCount'], spawnSubcommandLayer],
			'HeadQuarters': [5, '|pBB', ['clientId', 'U1', 'spawnCount'], spawnSubcommandLayer],
			'PlanetMap': [6, '|pBB', ['clientId', 'U1', 'spawnCount'], spawnSubcommandLayer],
			'AprilShipStatus': [7, '|pBB', ['clientId', 'U1', 'spawnCount'], spawnSubcommandLayer]
		}
	def settings(self):
		self.name = 'Spawn'
		self.pullCommandByte = True
		self.fieldBeforeSize = False
		self.sizeField = False
		self.order = '<'

class spawnSubcommandLayer(layerBase):
	def commands(self):
		return {
			'0': [0, '|X|?', ['netId', 'data'], False],
			'1': [1, '|X|?', ['netId', 'data'], False],
			'2': [2, '|X|?', ['netId', 'data'], False],
			'3': [3, '|X|?', ['netId', 'data'], False],
			'4': [4, '|X|?', ['netId', 'data'], False],
			'5': [5, '|X|?', ['netId', 'data'], False],
			'6': [6, '|X|?', ['netId', 'data'], False],
			'7': [7, '|X|?', ['netId', 'data'], False],	
		}

	def settings(self):
		self.name = 'SpawnSubcommand'
		self.pullCommandByte = True
		self.fieldBeforeSize = '|p' # why did you do this to us? This sucks to parse lol
		self.sizeField = "<H"
		self.order = '<'