from collections import Counter
from functools import reduce
from itertools import combinations, product
from json import dump, load
from math import radians, cos, sin, asin, sqrt
from random import shuffle
from time import time

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


def measure(santalong, santalat, ordering, children):
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


def powerset(s):
    ps = [tuple()]

    for n in range(1, len(s) + 1):
        for c in combinations(s, n):
            ps.append(c)

    return ps


def held_karp(santalong, santalat, group, children):
    seen = {}

    subsets = powerset([g.id for g in group])[1:]

    for subset in subsets:
        for c in subset:
            child = children[c]

            if len(subset) == 1:
                seen[(subset, c)] = (haversine(santalong, santalat, child.long, child.lat), [c])
                continue

            best = (10**9, [])

            for x in subset:
                if x == c:
                    continue

                subsubset = tuple([y for y in subset if y != c])
                childx = children[x]

                best = min(best, (seen[(subsubset, x)][0] + haversine(child.long, child.lat, childx.long, childx.lat), seen[(subsubset, x)][1] + [c]))

            seen[(subset, c)] = best

    best = (10**9, [])

    for c in group:
        lastleg = haversine(santalong, santalat, c.long, c.lat)

        if seen[(subsets[-1], c.id)][0] + lastleg < best[0]:
            best = (seen[(subsets[-1], c.id)][0] + lastleg, seen[(subsets[-1], c.id)][1])
    
    return best[1]


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


def cluster(santapacity, santalong, santalat, children):
    clusters = { child.id: [child.id, [child], child.weight] for child in children.values() }

    def find(id):
        path = []

        while clusters[id][0] != id:
            path.append(id)
            id = clusters[id][0]

        for p in path:
            clusters[p][0] = id

        return id

    def union(a, b):
        anca = find(a)
        ancb = find(b)

        if anca == ancb:
            return

        clusters[anca][1] += clusters[ancb][1]
        clusters[anca][2] += clusters[ancb][2]
        clusters[ancb][0] = anca

    t = time()
    edges = []
    childlist = list(children.values())
    n = len(childlist)

    for i in range(n-1):
        a = childlist[i]
        for j in range(i+1, n):
            b = childlist[j]
            edges.append((haversine(a.long, a.lat, b.long, b.lat), a.id, b.id))

    print(f'Found edges in {time()-t} seconds.')
    t = time()
    edges.sort()
    print(f'Sorted them in {time()-t} seconds.')

    for _, a, b in edges:
        anca = find(a)
        ancb = find(b)

        if anca == ancb:
            continue

        if clusters[anca][2] + clusters[ancb][2] >= santapacity:
            continue

        union(anca, ancb)

    print(f'Clustering round took {time()-t} seconds.')

    out = []

    for k, v in clusters.items():
        if k == v[0]:
            out.append(v[1])

    return out


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


def random_ordering(santalong, santalat, group, n=10000):
    best = [10**9, group]

    for _ in range(n):
        shuffle(group)
        best = min(best, [measure(santalong, santalat, group, children), group])

    return best[1]


def nearest_neighbour(santalong, santalat, group):
    path = []

    while len(path) < len(group):
        best = [10**9, -1]

        for child in group:
            if child.id in path:
                continue

            best = min(best, [haversine(santalong, santalat, child.long, child.lat), child.id])

        path.append(best[1])

    return path

print('clustering')
t = time()
groups = cluster(santapacity, santalong, santalat, children)
print(f'took {time()-t} seconds to produce {len(groups)} groups.')
t = time()
heldkarpcutoff = 18
sizes = Counter()

for i, group in enumerate(groups):
    t = time()
    ordering = nearest_neighbour(santalong, santalat, group) if len(group) > heldkarpcutoff else held_karp(santalong, santalat, group, children)
    sizes[len(group)] += 1
    out.append(ordering)
    dist += measure(santalong, santalat, ordering, children)

print(f'Routed in {time()-t} seconds.')
print(sizes)

with open('out.txt', 'w') as g:
    for line in out:
        g.write('; '.join(line) + '\n')

print(dist, dist / 1000.0, len(out))