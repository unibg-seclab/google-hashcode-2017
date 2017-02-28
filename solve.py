from multiprocessing import Pool
from collections import defaultdict
from bisect import insort
import sys

class Cache:

    def __init__(self, capacity):
        self._capacity = capacity
        self.remaining = capacity
        self.videos = set()
        self.endpoints = set()

    @property
    def cost(self):
        return (2 - self.remaining / float(self._capacity)) ** 1.25

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

totrequests = 0
requests = [[0 for e in xrange(nendpoints)] for v in xrange(nvideos)]
for r in xrange(type_requests):
    video_id, endpoint_id, numrequests = row(int)
    requests[video_id][endpoint_id] += numrequests
    totrequests += numrequests

    for cache_id, latency_to_cache in endpoints[endpoint_id].iteritems():
        cache = caches[cache_id]

assert len(videos) == nvideos
assert len(latencies) == nendpoints
assert len(endpoints) == nendpoints

current_latencies = [[latencies[eid] for eid in xrange(nendpoints)] for vid in xrange(nvideos)]


def solve(video_id):
    video_size = videos[video_id]
    videorequests = requests[video_id]
    videolatencies = current_latencies[video_id]
    benefits = []

    for cache_id, cache in enumerate(caches):
        if video_size > cache.remaining: continue
        overall_benefit = 0

        for endpoint_id, endpoint in enumerate(endpoints):
            if cache_id not in endpoint: continue
            nrequest = videorequests[endpoint_id]
            if not nrequest: continue
            current_latency = videolatencies[endpoint_id]
            latency = endpoint[cache_id]

            if latency < current_latency:
                # punto da tarare
                latency_benefit = (current_latency - latency) * nrequest
                overall_benefit += latency_benefit

        overall_benefit_density = overall_benefit / (float(video_size) * caches[cache_id].cost)
        if overall_benefit: benefits.append((overall_benefit_density, overall_benefit, cache_id))

    benefits.sort(reverse=True)
    if not benefits: return 0, 0, None
    if len(benefits) == 1: return benefits[0]
    return benefits[0][0] - (0.1 * benefits[1][0]), benefits[0][1], benefits[0][2]

video_benefits = Pool(processes=8).map(solve, range(nvideos))
sorted_videos = [(b[0], video_id) for video_id, b in enumerate(video_benefits)]
sorted_videos.sort()   # remove from last!

try:
    score = 0.0
    used_size = 0
    total_size = cachesize * ncaches
    while sorted_videos:
        _, video_id = sorted_videos.pop()

        while True:
            benefit, deltascore, cache_id = solve(video_id)
            if benefit <= 0: break
            if len(sorted_videos) > 1 and sorted_videos[-2][0] > benefit:
                insort(sorted_videos, (benefit, video_id))
                break

            video_size = videos[video_id]
            used_size += video_size
            score += 1000.0 * deltascore / totrequests
            sys.stderr.write('length %d benefit %d [score: %d, full: %.2f%%]\n' %
                             (len(sorted_videos), benefit, score, 100.0 * used_size / total_size))

            cache = caches[cache_id]
            cache.videos.add(video_id)
            cache.remaining -= video_size

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

sys.stderr.write('score: %d, full: %.2f%%\n' % (score, 100.0 * used_size / total_size))
