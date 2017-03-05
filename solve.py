from multiprocessing import Pool
from collections import defaultdict
from operator import itemgetter
from bisect import insort
import sys
import os

import random
#seed = int(os.urandom(16).encode('hex'), 16)
seed = 8410677633984578494805627143684193372
random.seed(seed)
maxrand = random.random() * 5

class Cache:
    def __init__(self):
        self.videos = set()
        self.endpoints = set()

def row(fn):
    return map(fn, raw_input().strip().split())

def knapsack(items, capacity):
    table = [[0 for w in range(capacity + 1)] for j in xrange(len(items) + 1)]

    for j in xrange(1, len(items) + 1):
        item, wt, val = items[j-1]
        for w in xrange(1, capacity + 1):
            if wt > w:
                table[j][w] = table[j-1][w]
            else:
                table[j][w] = max(table[j-1][w],
                                  table[j-1][w-wt] + val)

    result = []
    w = capacity
    for j in range(len(items), 0, -1):
        was_added = table[j][w] != table[j-1][w]

        if was_added:
            item, wt, val = items[j-1]
            result.append(items[j-1])
            w -= wt

    return result, sum(map(itemgetter(2), result))

nvideos, nendpoints, type_requests, ncaches, cachesize = row(int)
videosize = row(int)

endpoints = []
latencies = []
caches = [Cache() for _ in xrange(ncaches)]

for endpoint_id in xrange(nendpoints):
    endpoint_latencies = {}
    latency_to_datacenter, connected_caches = row(int)
    latencies.append(latency_to_datacenter)

    for y in xrange(connected_caches):
        cache_id, latency_to_cache = row(int)
        endpoint_latencies[cache_id] = latency_to_cache
        caches[cache_id].endpoints.add(endpoint_id)
    endpoints.append(endpoint_latencies)

totrequests = 0
requests = [[0 for e in xrange(nendpoints)] for v in xrange(nvideos)]
for r in xrange(type_requests):
    video_id, endpoint_id, numrequests = row(int)
    requests[video_id][endpoint_id] += numrequests
    totrequests += numrequests

    for cache_id, latency_to_cache in endpoints[endpoint_id].iteritems():
        cache = caches[cache_id]

assert len(videosize) == nvideos
assert len(latencies) == nendpoints
assert len(endpoints) == nendpoints

def compute_video_values(cache_id):
    cache = caches[cache_id]
    values = defaultdict(int)

    for video_id in xrange(nvideos):
        videorequests = requests[video_id]
        if videosize[video_id] > cachesize: continue
        for endpoint_id in cache.endpoints:
            numrequests = videorequests[endpoint_id]
            if not numrequests: continue
            endpoint = endpoints[endpoint_id]
            current_latency = latencies[endpoint_id]

            for connected_cache_id, connected_cache_latency in endpoint.iteritems():
                if cache_id == connected_cache_id: continue
                if video_id in caches[connected_cache_id].videos:
                    if connected_cache_latency < current_latency:
                        current_latency = connected_cache_latency

            if endpoint[cache_id] < current_latency:
                values[video_id] += numrequests * (current_latency - endpoint[cache_id])

    return values

try:
    for iteration in xrange(100):
        sys.stderr.write('iteration %d\n' % iteration)

        cache_ids = range(ncaches)
        random.shuffle(cache_ids)

        for cache_id in cache_ids:
            cache = caches[cache_id]

            sys.stderr.write('cache %d\n' % cache_id)
            values = compute_video_values(cache_id)
            for key in values: values[key] *= (1 + random.random() * maxrand)
            items = [(video_id, videosize[video_id], values[video_id])
                    for video_id in values.iterkeys()]

            items_to_cache, benefit = knapsack(items, cachesize)
            videos_to_cache = set(map(itemgetter(0), items_to_cache))
            cache.videos = videos_to_cache
            sys.stderr.write('benefit: %s\n' % (1000.0 * benefit / totrequests))
except KeyboardInterrupt: pass


used_caches = sum(1 for cache in caches if cache.videos)
print used_caches

for cache_id, cache in enumerate(caches):
    if cache.videos:
        print cache_id, ' '.join(map(str, cache.videos))
