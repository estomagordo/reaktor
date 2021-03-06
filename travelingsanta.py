from collections import Counter
from functools import reduce
from itertools import combinations, product
from json import dump, load
from math import radians, cos, sin, asin, sqrt, acos
from random import shuffle
from time import time

from child import Child

heldkarpcutoff = 21
santalong = 29.315278
santalat = 68.073611
santapacity = 10**7
hill_climbing_limit = 2 * 10**5
clustering_loops = 1
clustering_criterion = 35 * 10**5
re_clustering_criterion = 95 * 10**5
random_clustering_attempts = 10**5

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


def wikimeasure(long1, lat1, long2, lat2):
    r = 6378

    lo1, la1, lo2, la2 = map(radians, (long1, lat1, long2, lat2))
    
    dlong = abs(lo1-lo2)
    dsigma = acos(sin(la1) * sin(la2) + cos(la1) * cos(la2) * cos(dlong))

    return dsigma * r


def rectangular_distance_sq(lon1, lat1, lon2, lat2):
    east = lon2 - lon1 if lon2 > lon1 else (180.0 - lon1) + (lon2 + 180.0)
    west = lon1 - lon2 if lon1 > lon2 else (180.0 - lon2) + (lon1 + 180.0)
    north = lat2 - lat1 if lat2 > lat1 else (90.0 - lat1) + (lat2 + 90.0)
    south = lat1 - lat2 if lat1 > lat2 else (90.0 - lat2) + (lat1 + 90.0)

    return min(east, west)**2 + min(north, south)**2


def distance(lon1, lat1, lon2, lat2):
    return wikimeasure(lon1, lat1, lon2, lat2)

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
        d += distance(long, lat, childlong, childlat)
        long, lat = childlong, childlat

    d += distance(long, lat, santalong, santalat)

    return d


def powerset(s):
    ps = [tuple()]

    for n in range(1, len(s) + 1):
        for c in combinations(s, n):
            ps.append(c)

    return ps


def held_karp(santalong, santalat, group, children):
    # Comparing with nearest neighbour without hill climbing first

    path = []

    while len(path) < len(group):
        best = [10**9, None]

        for child in group:
            if child in path:
                continue

            best = min(best, [distance(santalong, santalat, child.long, child.lat), child])

        path.append(best[1])

    nndist = measure(santalong, santalat, [c.id for c in path], children)

    seen = {}

    subsets = powerset([g.id for g in group])[1:]

    for subset in subsets:
        for c in subset:
            child = children[c]

            if len(subset) == 1:
                seen[(subset, c)] = (distance(santalong, santalat, child.long, child.lat), [c])
                continue

            best = (10**9, [])

            for x in subset:
                if x == c:
                    continue

                subsubset = tuple([y for y in subset if y != c])
                childx = children[x]

                best = min(best, (seen[(subsubset, x)][0] + distance(child.long, child.lat, childx.long, childx.lat), seen[(subsubset, x)][1] + [c]))

            seen[(subset, c)] = best

    best = (10**9, [])

    for c in group:
        lastleg = distance(santalong, santalat, c.long, c.lat)

        if seen[(subsets[-1], c.id)][0] + lastleg < best[0]:
            best = (seen[(subsets[-1], c.id)][0] + lastleg, seen[(subsets[-1], c.id)][1])
    
    print(f'HK optimal {100.0 * measure(santalong, santalat, best[1], children) / nndist}% of simple nearest neighbour.')
    
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


def other_clustering(santapacity, childlist):
    # cue knapsack
    pass


def cluster_round(santapacity, childlist):
    clusters = { child.id: [child.id, [child], child.weight] for child in childlist }

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
    n = len(childlist)

    for i in range(n-1):
        a = childlist[i]
        for j in range(i+1, n):
            b = childlist[j]
            edges.append((distance(a.long, a.lat, b.long, b.lat), a.id, b.id))

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


def cluster(santapacity, santalong, santalat, children):
    clusters = []
    childlist = list(children.values())
    
    t = time()
    clustered = cluster_round(santapacity, childlist)
    childlist = []

    for cluster in clustered:
        if sum(c.weight for c in cluster) > clustering_criterion:
            clusters.append(cluster)
        else:
            for c in cluster:
                childlist.append(c)

    print(f'After clustering by proximity, {len(clusters)} have been found. {len(childlist)} remain. This took {time()-t} seconds.')

    t = time()

    for x in range(random_clustering_attempts):
        if x > 0 and x % 10000 == 0:
            print(f'Random clustering attempt {x}.')

        if not childlist:
            break

        shuffle(childlist)

        clusterattempt = []
        clusterweight = 0.0
        childids = set()

        for child in childlist:
            if clusterweight + child.weight < santapacity:
                clusterattempt.append(child)
                clusterweight += child.weight
                childids.add(child.id)

        if clusterweight > re_clustering_criterion:
            clusters.append(clusterattempt)
            childlist = [c for c in childlist if c.id not in childids]
            print(f'cluster of weight {clusterweight} and size {len(clusterattempt)} found!')

    print(f'Random clustering took {time()-t} seconds. {len(childlist)} children remain.')
    
    if childlist:
        t = time()
        clusters += cluster_round(santapacity, childlist)
        print(f'Final clustering took {time()-t} seconds.')
    
    return clusters


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


def hill_climbing(santalong, santalat, path, children):
    t = tuple([p.id for p in path])
    td = measure(santalong, santalat, t, children)
    best = [td, t]
    seen = {t}
    frontier = [(t,td)]
    n = len(t)

    for p, pd in frontier:
        if len(frontier) > hill_climbing_limit:
            break
        for i in range(n-1):
            a = p[i]
            for j in range(i+1, n):
                b = p[j]
                pl = list(p)
                pdelta = tuple(pl[:i] + [b] + pl[i+1:j] + [a] + pl[j+1:])
                
                if pdelta in seen:
                    continue

                d = measure(santalong, santalat, pdelta, children)

                if d < pd:
                    seen.add(pdelta)                    
                    frontier.append((pdelta, d))
                    best = min(best, [d, pdelta])

    print(f'Hill climbed {len(frontier)} alternatives. Ending up at { 100.0 * best[0] / td}% of the original.')
    
    return best[1]


def nearest_neighbour(santalong, santalat, group, children):
    path = []

    while len(path) < len(group):
        best = [10**9, None]

        for child in group:
            if child in path:
                continue

            best = min(best, [distance(santalong, santalat, child.long, child.lat), child])

        path.append(best[1])

    return hill_climbing(santalong, santalat, path, children)


out = []

with open('out.txt') as f:
    i = 1

    for line in f.readlines():
        items = line.split()
        
        if len(items) in [20, 21]:
            group = []            

            for item in items:
                group.append(children[item[:-1] if item[-1] == ';' else item])

            print(f'Routing group {i} (size {len(group)}), using Held Karp')
            t = time()
            ordering = held_karp(santalong, santalat, group, children)                
            out.append(ordering)                
            print(f'Took {time()-t} seconds.')
        else:
            out.append(line)

        i =+ 1

# print('clustering')
# t = time()
# groups = cluster(santapacity, santalong, santalat, children)

# print(f'took {time()-t} seconds to produce {len(groups)} groups.')
# t = time()
# sizes = Counter()

# for i, group in enumerate(groups):
#     print(f'Routing group {i+1} of {len(groups)} (size {len(group)}), using {"Held Karp" if len(group) <= heldkarpcutoff else "Nearest neighbour and hill climbing"}')
#     t = time()
#     ordering = nearest_neighbour(santalong, santalat, group, children) if len(group) > heldkarpcutoff else held_karp(santalong, santalat, group, children)
#     sizes[len(group)] += 1
#     out.append(ordering)
#     dist += measure(santalong, santalat, ordering, children)
#     print(f'Took {time()-t} seconds.')

# print(sizes)

with open('out.txt', 'w') as g:
    for line in out:
        g.write('; '.join(line) + '\n')