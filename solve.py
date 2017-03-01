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
        return (2 - self.remaining / float(self._capacity))# ** 1.25

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

def solve_specific(cache_id, video_id):
    cache = caches[cache_id]
    video_size = videos[video_id]
    videorequests = requests[video_id]
    videolatencies = current_latencies[video_id]
    if video_size > cache.remaining: return 0, 0
    benefit = 0

    for endpoint_id, endpoint in enumerate(endpoints):
        if cache_id not in endpoint: continue
        nrequest = videorequests[endpoint_id]
        if not nrequest: continue
        current_latency = videolatencies[endpoint_id]
        latency = endpoint[cache_id]

        if latency < current_latency:
            benefit += (current_latency - latency) * nrequest

    benefit_density = benefit / (float(video_size) * cache.cost)
#    benefit_density = benefit / float(video_size)
    return benefit_density, benefit

def compute_cache_benefits(cache_id):
    video_solutions = [solve_specific(cache_id, video_id) for video_id in xrange(nvideos)]
    video_benefits = [(b[0], video_id) for video_id, b in enumerate(video_solutions)]
    video_benefits.sort() # remove from last!
    return video_benefits

cache_benefits = Pool().map(compute_cache_benefits, range(ncaches))

def solve(cache_id):
    cache = caches[cache_id]
    benefits = cache_benefits[cache_id]
    available = cache.remaining
    tot_deltascore = 0
    theoretical_available_benefit_density = 0
    chosen = []

    while benefits:
        benefit, video_id = benefits.pop()
        if video_id in cache.videos: continue
        benefit, deltascore = solve_specific(cache_id, video_id)
        if benefit <= 0: continue
        if benefits and benefits[-1][0] > benefit:
            insort(benefits, (benefit, video_id))
        else:
            chosen.insert(0, (benefit, video_id))
            video_size = videos[video_id]
            if video_size <= available:
                available -= video_size
                tot_deltascore += deltascore
            else:
                theoretical_available_benefit_density = benefit
                break

    if not chosen: return 0, 0, None

    video_id = chosen[-1][1]
    benefit, deltascore = solve_specific(cache_id, video_id)

#    solvebenefit = sum(b * videos[vid] for b, vid in chosen)
#    solvebenefit += theoretical_available_benefit_density * available
#    solvebenefit = solvebenefit / ((1+available) ** 0.1)

    chosen_size = sum(videos[vid] for b, vid in chosen)
    avg_benefit = sum(b * videos[vid] for b, vid in chosen[:-1]) / float(chosen_size)
    if avg_benefit: benefit = benefit * (benefit / avg_benefit)
    else: benefit = benefit * 10

    result = (benefit, deltascore, video_id)
    benefits.extend(chosen)
    return result

sorted_caches = [(solve(cache_id)[0], cache_id) for cache_id in xrange(ncaches)]
sorted_caches.sort()   # remove from last!

try:
    score = 0.0
    used_size = 0
    total_size = cachesize * ncaches
    while sorted_caches:
        _, cache_id = sorted_caches.pop()

        while True:
            benefit, deltascore, video_id = solve(cache_id)
            if benefit <= 0: break
            if sorted_caches and sorted_caches[-1][0] > benefit:
                insort(sorted_caches, (benefit, cache_id))
                break

            video_size = videos[video_id]
            used_size += video_size
            score += 1000.0 * deltascore / totrequests
            sys.stderr.write('length %d benefit %d [score: %d, full: %.2f%%]\n' %
                             (len(sorted_caches), benefit, score, 100.0 * used_size / total_size))

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
