from functools import reduce
from json import dump, load
from math import radians, cos, sin, asin, sqrt

from child import Child

# Slightly modified from https://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6378 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

santalong = 29.315278
santalat = 68.073611
santapacity = 10**7

children = {}

with open('nicelist.txt') as f:
    for line in f.readlines():
        vals = line.split(';')
        id = vals[0]
        long = float(vals[1])
        lat = float(vals[2])
        weight = int(vals[3])

        children[id] = Child(id, long, lat, weight)

out = []
dist = 0.0


def measure(santalong, santalat, ordering):
    d = 0.0

    long = santalong
    lat = santalat

    for i in ordering:
        child = children[i]
        childlong, childlat = child.long, child.lat
        d += haversine(long, lat, childlong, childlat)
        long, lat = childlong, childlat

    d += haversine(long, lat, santalong, santalat)

    return d


def get_ordering(santalong, santalat, group):
    group.sort(key=lambda child: -haversine(santalong, santalat, child.long, child.lat))

    return [g.id for g in group]


def get_granular_group(santapacity, children):
    groups = []
    group = [[], 0.0]

    for child in children:
        if group[1] + child.weight > santapacity:
            groups.append(group[0])
            group = [[child], child.weight]
        else:
            group[0].append(child)
            group[1] += child.weight

    if group[0]:
        groups.append(group[0])

    return groups


def get_groups(santapacity, santalong, santalat, children):
    topleft = []
    topright = []
    botleft = []
    botright = []

    for child in children.values():
        left = -santalong <= child.long <= santalong
        up = -santalat <= child.lat <= santalat

        if left:
            if up:
                topleft.append(child)
            else:
                botleft.append(child)
        elif up:
            topright.append(child)
        else:
            botright.append(child)

    return reduce(lambda a,b: a + b, [get_granular_group(santapacity, g) for g in [topleft, topright, botleft, botright]])


for group in get_groups(santapacity, santalong, santalat, children):
    ordering = get_ordering(santalong, santalat, group)
    out.append(ordering)
    dist += measure(santalong, santalat, ordering)

with open('out.txt', 'w') as g:
    for line in out:
        g.write('; '.join(line) + '\n')

print(dist, dist / 1000.0, len(out))