from collections import defaultdict
from bisect import insort
import sys

class Cache:

    def __init__(self, capacity):
        self.remaining = capacity
        self.videos = set()

def row(fn):
    return map(fn, raw_input().strip().split())

nvideos, nendpoints, type_requests, ncaches, cachesize = row(int)
videos = row(int)
endpoints = []

latencies = []
for i in xrange(nendpoints):
    endpoint = {}
    latency, ncaches_e = row(int)
    latencies.append(latency)

    for y in xrange(0, ncaches_e):
        cache_id, latcache = row(int)
        endpoint[cache_id] = latcache
    endpoints.append(endpoint)

cache_to_endpoints = defaultdict(set)
for endpoint_id, endpoint in enumerate(endpoints):
    for cache_id in endpoint.iterkeys():
        cache_to_endpoints[cache_id].add(endpoint_id)

requests = [[0 for e in xrange(nendpoints)] for v in xrange(nvideos)]
current_latencies = [[latencies[eid] for eid in xrange(nendpoints)] for vid in xrange(nvideos)]

for r in xrange(type_requests):
    video_id, endpoint_id, numrequests = row(int)
    requests[video_id][endpoint_id] += numrequests

assert len(videos) == nvideos
assert len(latencies) == nendpoints
assert len(endpoints) == nendpoints

caches = [Cache(cachesize) for _ in xrange(ncaches)]

def solve(video_id, video_size):
    best_benefit = float('-inf')
    best_cache = None
    videorequests = requests[video_id]
    videolatencies = current_latencies[video_id]

    for cache_id, cache in enumerate(caches):
        if video_size > cache.remaining: continue
        overall_benefit = 0

        for endpoint_id, endpoint in enumerate(endpoints):
            if cache_id not in endpoint: continue
            nrequest = videorequests[endpoint_id]
            if not nrequest: continue
            #current_latency = latencies[endpoint_id]    # datacenter -> endpoint
            current_latency = videolatencies[endpoint_id]
            latency = endpoint[cache_id]

            if latency < current_latency:
                # punto da tarare
                latency_benefit = (current_latency - latency) * nrequest
                overall_benefit += latency_benefit

        overall_benefit_density = overall_benefit / float(video_size)
        if overall_benefit_density > best_benefit:
            best_benefit = overall_benefit_density
            best_cache = cache_id

    return best_benefit, best_cache


for video_id, video_size in enumerate(videos):
    reqs = 0
    for endpoint_id in xrange(nendpoints):
        reqs += requests[video_id][endpoint_id]

sorted_videos = [(solve(video_id, videos[video_id])[0], video_id) for video_id in xrange(nvideos)]
sorted_videos.sort()   # remove from last!

try:
    while sorted_videos:
        _, video_id = sorted_videos.pop()
        video_size = videos[video_id]
        sys.stderr.write('length %d\n' % len(sorted_videos))

        while True:
            benefit, cache_id = solve(video_id, video_size)
            sys.stderr.write('length %d benefit %g\n' % (len(sorted_videos), benefit))
            if benefit <= 0: break
            if sorted_videos and sorted_videos[-1][0] > benefit:
                insort(sorted_videos, (benefit, video_id))
                break

            cache = caches[cache_id]
            cache.videos.add(video_id)
            cache.remaining -= video_size

            for endpoint_id in cache_to_endpoints[cache_id]:
                #requests[video_id][endpoint_id] = 0
                current_latencies[video_id][endpoint_id] = min(current_latencies[video_id][endpoint_id],
                                                               endpoints[endpoint_id][cache_id])

except KeyboardInterrupt:
    pass


used_caches = sum(1 for cache in caches if cache.videos)
print used_caches

for cache_id, cache in enumerate(caches):
    if cache.videos:
        print cache_id, ' '.join(map(str, cache.videos))
