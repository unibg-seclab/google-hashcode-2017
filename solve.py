from multiprocessing import Pool
from collections import defaultdict, namedtuple
from bisect import insort
import heapq
import sys

class Cache:

    def __init__(self, capacity):
        self._capacity = capacity
        self.remaining = capacity
        self.videos = set()
        self.endpoints = set()
        self.benefits = defaultdict(int)

    @property
    def cost(self):
        return 1

def row(fn):
    return map(fn, raw_input().strip().split())

nvideos, nendpoints, type_requests, ncaches, cachesize = row(int)
videos = row(int)

endpoints = []
latencies = []
caches = [Cache(cachesize) for _ in xrange(ncaches)]

for endpoint_id in xrange(nendpoints):
    endpoint_latencies = {}
    latency_to_datacenter, connected_caches = row(int)
    latencies.append(latency_to_datacenter)

    for y in xrange(connected_caches):
        cache_id, latency_to_cache = row(int)
        endpoint_latencies[cache_id] = latency_to_cache
        caches[cache_id].endpoints.add(endpoint_id)
    endpoints.append(endpoint_latencies)

raw_requests = set() # just for last iteration
requests = [[0 for e in xrange(nendpoints)] for v in xrange(nvideos)]
for r in xrange(type_requests):
    if r % 1000 == 0: sys.stderr.write("%.2f\n" % (float(r) / type_requests))
    video_id, endpoint_id, numrequests = row(int)
    video_size = videos[video_id]
    #if video_size > cachesize: continue       # skips videos too big to cache
    requests[video_id][endpoint_id] += numrequests
    raw_requests.add((video_id,endpoint_id))

    for cache_id, latency_to_cache in endpoints[endpoint_id].iteritems():
        cache = caches[cache_id]
        request_benefit = (latencies[endpoint_id] - latency_to_cache) * numrequests
        if request_benefit > 0:
            cache.benefits[video_id] += request_benefit / float(video_size)

assert len(videos) == nvideos
assert len(latencies) == nendpoints
assert len(endpoints) == nendpoints

current_latencies = [[latencies[eid] for eid in xrange(nendpoints)] for vid in xrange(nvideos)]

for cache_id, cache in enumerate(caches):
    cache.benefits = sorted((b, vid) for vid, b in cache.benefits.iteritems() if b > 0)
    requested_size = sum(videos[vid] for b, vid in cache.benefits)
    if requested_size <= cachesize:
        cache.videos = [vid for vid, b in cache.benefits]
        cache.remaining = 0

def solve(video_id, cache_id):
    video_size = videos[video_id]
    videorequests = requests[video_id]
    videolatencies = current_latencies[video_id]

    if video_size > cache.remaining: return 0
    benefit = 0

    for endpoint_id, endpoint in enumerate(endpoints):
        if cache_id not in endpoint: continue
        nrequest = videorequests[endpoint_id]
        if not nrequest: continue
        current_latency = videolatencies[endpoint_id]
        latency = endpoint[cache_id]

        if latency < current_latency:
            # punto da tarare
            benefit += (current_latency - latency) * nrequest

    #overall_benefit_density = benefit / (float(video_size) * caches[cache_id].cost)
    return benefit / float(video_size)


benefits = [(-b, vid, cid) for cid, cache in enumerate(caches) for b, vid in cache.benefits]
heapq.heapify(benefits)

for b in benefits: sys.stderr.write("%d\n" % -b[0])

try:

    while benefits:
        sys.stderr.write("%d\n" % len(benefits))
        _, video_id, cache_id = heapq.heappop(benefits)
        benefit = solve(video_id, cache_id)

        if benefit <= 0: continue
        second = heapq.heappop(benefits)
        heapq.heappush(benefits, second)
        if benefits and -second[0] > benefit:
            sys.stderr.write('relocate\n')
            heapq.heappush(benefits, (-benefit, video_id, cache_id))
            continue

        sys.stderr.write('length %d benefit %d\n' % (len(benefits), benefit))
        cache = caches[cache_id]
        cache.videos.add(video_id)
        cache.remaining -= videos[video_id]

        for endpoint_id in caches[cache_id].endpoints:
            current_latencies[video_id][endpoint_id] = \
                    min(current_latencies[video_id][endpoint_id],
                        endpoints[endpoint_id][cache_id])

except KeyboardInterrupt: pass


used_caches = sum(1 for cache in caches if cache.videos)
print used_caches

for cache_id, cache in enumerate(caches):
    if cache.videos:
        print cache_id, ' '.join(map(str, cache.videos))

totrequests = 0
totsaved = 0
for video_id, endpoint_id in raw_requests:
    nrequests = requests[video_id][endpoint_id]
    if nrequests:
        original_latency = latencies[endpoint_id]
        current_latency = current_latencies[video_id][endpoint_id]
        assert current_latency <= original_latency
        totrequests += nrequests
        totsaved += (original_latency - current_latency) * nrequests

sys.stderr.write('score %d\n' % (1000.0 * totsaved / totrequests))
