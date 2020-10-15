# amongUsParser

Among Us packet parsing library and game engine

Simple packet parsing example
-----------------------------

from amongUsParser import parse ## Load parser	

tree = parse(b'\x01\x00\x61\x0b\x00\x05\x24\xe1\x36\x80\x04\x00\x02\xc2\x01\x0b\x08') ## Contents of packet

tree.pprint() ## Pretty print data
<blockquote>
Output:

    Hazil
        Command Leaf
        - ReliableData
        -- seq : 97
        InnerNet
                Command Leaf
                - GameData
                -- gameId : 2151080228
                GameData
                        Command Leaf
                        - RpcCall
                        -- ownerId : 194
                        RPC
                                Command Leaf
                                - ReportDeadBody
                                -- playerId : 8
</blockquote>
read-pcap.py
------------
read-pcap.py shows an example of dumping out pcap files and displaying the data structures inside of the packets
example game pcaps and resulting data structure dumps are included in the pcap folder

read-live.py
------------
read-live.py contains a basic example of reading live data using scapy, feeding it to the game engine, then using the callback system for simplified actions

Other examples
--------------
Look in my repo for the discord bot for a fully featured example


Game engine callbacks
---------------------

List of game engine callbacks

	Player updated
		Exiled
		Murdered
		Murder
		SetSkin
		SetHat
		SetPet
		SetColor
		Infected
		Chat (contains 'message' param)
		SetName

	Game updated
		Reset
		StartGame
		EndGame
		JoinedGame
		GameSettings
		StartMeeting
		EndMeeting

