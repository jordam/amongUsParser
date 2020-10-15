import math

def flatten(tree, nodes): ## fills nodes array with references to all of the nodes in the tree
	nodes.append(tree)
	for child in tree.children:
		flatten(child, nodes)

def unpack(data):
	readMore = True
	shift = 0
	output = 0
	on = 0
	while readMore:
		b = data[on]
		on += 1
		if b >= 128:
			readMore = True
			b ^= 128
		else:
			readMore = False
		output |= b << shift
		shift += 7
	return output, data[on:]

def pack(data):
	d = int.from_bytes(data, 'little')
	return packInt(d)

def packInt(d):
	output = b''
	while d > 0:
		b = d & 255
		if d >= 128:
			b |= 128
		output += bytes([b])
		d >>=7
	return output

def invert(d):
	o = {}
	for dk in d.keys():
		o[d[dk][0]] = dk
	return o

def intToGameCode(input):
	V2 = "QWXRTYLPESDFGHUJKZOCVBINMA"

	a = input & 1023
	b = (input >> 10) & 1048575
	
	vals = [
		V2[a % 26],
		V2[math.floor(a / 26)],
		V2[math.floor(b % 26)],
		V2[math.floor(b / 26 % 26)],
		V2[math.floor(b / (26*26) % 26)],
		V2[math.floor(b / (26*26*26) % 26)]
		]
	code = "".join(vals)
	return code

def gameCodeToInt(code):
	dv = "QWXRTYLPESDFGHUJKZOCVBINMA"
	dd = {}
	i = 0
	for c in dv:
		dd[c] = i
		i += 1
		
	x = []
	i = 0
	for c in code:
		x.append(dd[c])
	one = ( x[0] + (26*x[1]) ) & 1023
	two = (x[2] + (26 * (x[3] + 26 * (x[4] + (26 * x[5])))))
	res = (one | ((two << 10) & 1073740800) | 2147483648)
	return res