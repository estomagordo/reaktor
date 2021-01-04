def parsebyte(byte):
    return int(''.join(byte), 2)


def chunk(l, size):
    out = []

    for x in range(0, len(l), 8):
        out.append(l[x:x+8])

    return out


def interpret(channel):
    chunks = chunk(channel, 8)
    bytes = [parsebyte(byte) for byte in chunks]
    n = len(bytes)

    pos = 0

    while bytes[pos] >= n:
        pos += 1

    while bytes[pos] < n:
        pos = bytes[pos]

    return chr(bytes[pos])

channels = []

with open('humanoidhunt.txt') as f:
    for line in f:
        channels.append(line.rstrip())

print(''.join(map(interpret, channels)))