from collections import Counter
from itertools import combinations


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

signal2 = ''

with open('signal2.txt') as f:
    signal2 = f.readline().rstrip()

startcounter = Counter(signal2)
c = startcounter.most_common(1)[0][0]

base = c

while True:
    counter = Counter([signal2[x+1] for x in range(len(signal2)-1) if signal2[x] == c])
    c = counter.most_common(1)[0][0]

    if c == ';':
        break

    base += c

print(base)

neuralstrands = []

with open('neuralstrands.txt') as f:
    for line in f:
        neuralstrands.append(line.rstrip())

safe = set()
walls = set()
finish = set()
startx = -1
starty = -1

for strand in neuralstrands:
    if ' ' in strand:
        coords, path = strand.split()
        x, y = map(int, coords.split(','))
        steps = path.split(',')

        for step in steps:
            if step == 'F':
                finish.add((x, y))
            elif step == 'S':
                startx = x
                starty = y
            elif step == 'X':
                walls.add((x, y))
            else:
                safe.add((x, y))

                if step == 'D':
                    y += 1
                elif step == 'U':
                    y -= 1
                elif step == 'R':
                    x += 1
                else:
                    x -= 1

        if steps[-1] in 'DURL':
            safe.add((x, y))
    else:
        x, y = map(int, strand.split(','))
        safe.add((x, y))

seen = {(startx, starty)}
frontier = [(startx, starty, '')]
closest = 10**10

for x, y, path in frontier:
    d = min(abs(f[0]-1) + abs(f[1]-y) for f in finish)
    if d < closest:
        print(d, x, y)
        closest = d
    if (x, y) in finish:
        print(path)
        break

    if (x+1, y) in safe and (x+1, y) not in seen:
        seen.add((x+1, y))
        frontier.append((x+1, y, path + 'R'))
    if (x-1, y) in safe and (x-1, y) not in seen:
        seen.add((x-1, y))
        frontier.append((x-1, y, path + 'L'))
    if (x, y+1) in safe and (x, y+1) not in seen:
        seen.add((x, y+1))
        frontier.append((x, y+1, path + 'D'))
    if (x, y-1) in safe and (x, y-1) not in seen:
        seen.add((x, y-1))
        frontier.append((x, y-1, path + 'U'))

print(len(seen))
print(walls)
print(finish)
minx = min(p[0] for p in {(startx,starty)}|walls|finish)
maxx = max(p[0] for p in {(startx,starty)}|walls|finish)
miny = min(p[1] for p in {(startx,starty)}|walls|finish)
maxy = max(p[1] for p in {(startx,starty)}|walls|finish)
print(minx, maxx, miny, maxy)

for y in range(miny, maxy+1):
    row = []
    for x in range(minx, maxx+1):
        row.append('#' if (x, y) in walls else 'S' if x == startx and y == starty else 'F' if (x, y) in finish else '.' if (x, y) in safe else ' ')
    print(''.join(row))