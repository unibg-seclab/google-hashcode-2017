from multiprocessing import Pool
from collections import defaultdict
from operator import itemgetter
from bisect import bisect_left
import random
import math
import sys
import os

#seed = int(os.urandom(16).encode('hex'), 16)
#random.seed(seed)
random.seed(0)

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
requests = defaultdict(lambda: defaultdict(int))
for r in xrange(type_requests):
    video_id, endpoint_id, numrequests = row(int)
    requests[video_id][endpoint_id] += numrequests
    totrequests += numrequests

    for cache_id, latency_to_cache in endpoints[endpoint_id].iteritems():
        cache = caches[cache_id]

assert len(videosize) == nvideos
assert len(latencies) == nendpoints
assert len(endpoints) == nendpoints

_current_latencies = [[[] for eid in xrange(nendpoints)] for vid in xrange(nvideos)]

def get_current_latency(video_id, endpoint_id, excluding_cache=None):
    latency_pairs = _current_latencies[video_id][endpoint_id]
    idx = 0
    while idx < len(latency_pairs):
        latency, cache_id = latency_pairs[idx]
        if cache_id == excluding_cache: idx += 1
        elif video_id not in caches[cache_id].videos: latency_pairs.pop(idx)
        else: return latency
    return latencies[endpoint_id]

def update_current_latency(video_id, endpoint_id, cache_id):
    latency_pairs = _current_latencies[video_id][endpoint_id]
    latency = endpoints[endpoint_id][cache_id]
    latency_pair = (latency, cache_id)
    idx = bisect_left(latency_pairs, latency_pair)
    if idx == len(latency_pairs) or latency_pairs[idx] != latency_pair:
        latency_pairs.insert(idx, latency_pair)

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
            current_latency = get_current_latency(video_id, endpoint_id, excluding_cache=cache_id)
            if endpoint[cache_id] < current_latency:
                values[video_id] += numrequests * (current_latency - endpoint[cache_id])

    return values

def compute_score():
    score = 0
    for video_id in xrange(nvideos):
        for endpoint_id, numrequests in requests[video_id].iteritems():
            latency = latencies[endpoint_id]
            current_latency = min(latency, get_current_latency(video_id, endpoint_id))
            score += (latency - current_latency) * numrequests
    return int(math.floor(1000.0 * score / totrequests))

def make_output():
    print sum(1 for cache in caches if cache.videos)
    for cache_id, cache in enumerate(caches):
        if cache.videos: print cache_id, ' '.join(map(str, cache.videos))

try:
    for iteration in xrange(100):
        cache_ids = range(ncaches)
        random.shuffle(cache_ids)

        for cache_id in cache_ids:
            cache = caches[cache_id]

            values = compute_video_values(cache_id)
            items = [(video_id, videosize[video_id], values[video_id])
                    for video_id in values.iterkeys()]

            items_to_cache, benefit = knapsack(items, cachesize)
            videos_to_cache = set(map(itemgetter(0), items_to_cache))
            cache.videos = videos_to_cache
            sys.stderr.write('cache: %d benefit: %d\n' % (cache_id, 1000.0 * benefit / totrequests))

            for video_id in cache.videos:
                for endpoint_id in cache.endpoints:
                    update_current_latency(video_id, endpoint_id, cache_id)

        sys.stderr.write('iteration %d score: %d\n' % (iteration, compute_score()))

except KeyboardInterrupt: pass
finally: make_output()
