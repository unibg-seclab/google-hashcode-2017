#from tqdm import tqdm

class Cache:

    def __init__(self, capacity):
        self.remaining = capacity
        self.videos = set()

#nvideos, nendpoints, nrequests, ncaches, cachesize = 5, 2, 4, 3, 100
#videos1 = [50, 50, 80, 30, 110]
## 
#latencies1 = [1000, 500]
#endpoints1 = [{0: 100, 2: 200, 1: 300},
#             {}]
#requests1 = {(3, 0): 1500, (0, 1): 1000, (4, 0): 500, (1, 0): 1000}

import sys
fname = sys.argv[1]
fp = open(fname)

def row(fn):
    return map(fn, fp.readline().strip().split())


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

requests = [[0 for e in xrange(nendpoints)] for v in xrange(nvideos)]

for r in xrange(type_requests):
    video_id, endpoint_id, numrequests = row(int)
    requests[video_id][endpoint_id] += numrequests

assert len(videos) == nvideos
assert len(latencies) == nendpoints
assert len(endpoints) == nendpoints
#assert len(requests) == type_requests
# 
# print latencies
# print endpoints
# print requests
# 
# assert latencies == latencies1
# assert endpoints == endpoints1
# assert requests == requests1
# assert videos == videos1
# 
caches = [Cache(cachesize) for _ in xrange(ncaches)]

def solve(video_id, video_size):
    best_benefit = float('-inf')
    best_cache = None
    videorequests = requests[video_id]

    for cache_id, cache in enumerate(caches):
        if video_size > cache.remaining: continue
        overall_benefit = 0

        for endpoint_id, endpoint in enumerate(endpoints):
            if cache_id not in endpoint: continue
            nrequest = videorequests[endpoint_id]
            if not nrequest: continue
            current_latency = latencies[endpoint_id]    # datacenter -> endpoint

            for connected_cache_id, connected_cache_latency in endpoint.iteritems():
                if video_id in caches[connected_cache_id].videos:
                    current_latency = min(current_latency, connected_cache_latency)

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

requestsdensity = {}

for video_id, video_size in enumerate(videos):
    reqs = 0
    for endpoint_id in xrange(nendpoints):
        reqs += requests[video_id][endpoint_id]
    requestsdensity[video_id] = reqs / float(video_size)

sorted_videos = [(requestsdensity[video_id], video_id) for video_id in xrange(nvideos)]
sorted_videos.sort(reverse=True)

i = 0
import sys

try:
    for _, video_id in sorted_videos:
        video_size = videos[video_id]
        sys.stderr.write('i %d\n' % i)
        i += 1

        j = 0
        while True:
            benefit, cache_id = solve(video_id, video_size)
            if benefit <= 0: break
            sys.stderr.write('times %d\n' % j)
            j += 1
            #print benefit

            cache = caches[cache_id]
            cache.videos.add(video_id)
            cache.remaining -= videos[video_id]
            #print 'cache_id %d, video_id: %d' % (cache_id, video_id)

except KeyboardInterrupt:
    pass


used_caches = sum(1 for cache in caches if cache.videos)
print used_caches

for cache_id, cache in enumerate(caches):
    if cache.videos:
        print cache_id, ' '.join(map(str, cache.videos))

