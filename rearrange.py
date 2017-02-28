from collections import defaultdict
from multiprocessing import Pool
import multiprocessing
import signal
import sys

multiprocessing.log_to_stderr()

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

class Cache:

    def __init__(self, capacity):
        self._capacity = capacity
        self.remaining = capacity
        self.videos = set()
        self.endpoints = set()

class Endpoint:

    def __init__(self):
        self.requests = defaultdict(int)
        self.caches = {}

def row(fn, fp=sys.stdin):
    return map(fn, fp.readline().strip().split())

input_filename, solution_filename = sys.argv[1:3]

with open(input_filename) as fp:

    nvideos, nendpoints, nrequests, ncaches, cachesize = row(int, fp)

    totrequests = 0
    videos = row(int, fp)
    all_videos = frozenset(range(nvideos))
    endpoints = [Endpoint() for _ in xrange(nendpoints)]
    caches = [Cache(cachesize) for _ in xrange(ncaches)]

    for endpoint_id, endpoint in enumerate(endpoints):
        endpoint.latency, nconnections = row(int, fp)

        for _ in xrange(nconnections):
            cache_id, latency_to_cache = row(int, fp)
            endpoint.caches[cache_id] = latency_to_cache
            caches[cache_id].endpoints.add(endpoint_id)

    for request_id in xrange(nrequests):
        video_id, endpoint_id, numrequests = row(int, fp)
        endpoints[endpoint_id].requests[video_id] += numrequests
        totrequests += numrequests

with open(solution_filename) as fp:
    (used_caches,) = row(int, fp)
    for _ in xrange(used_caches):
        line = row(int, fp)
        cache = caches[line[0]]
        for video_id in line[1:]:
            cache.videos.add(video_id)
            cache.remaining -= videos[video_id]
            assert cache.remaining >= 0


def compute_latencies(video_id):
    current_latency = [e.latency for e in endpoints]
    for cache_id, cache in enumerate(caches):
        if video_id in cache.videos:
            for endpoint_id in cache.endpoints:
                current_latency[endpoint_id] = \
                    min(current_latency[endpoint_id],
                        endpoints[endpoint_id].caches[cache_id])
    return current_latency


def compute_delta_per_cache(args):
    current_latency, cache_id = args
    cache = caches[cache_id]
    del_costs = []
    add_benefits = []

    # what if I remove a cached video?
    for video_id in cache.videos:
        delta = 0

        for endpoint_id in cache.endpoints:
            endpoint = endpoints[endpoint_id]
            numrequests = endpoint.requests.get(video_id, 0)
            if numrequests and endpoint.caches[cache_id] == current_latency[video_id][endpoint_id]:
                # find best cache_server excluding cache_id
                best_cache_latency = endpoint.latency
                for new_cache_id, new_cache_latency in endpoint.caches.iteritems():
                    if new_cache_id != cache_id and new_cache_latency < best_cache_latency:
                        if video_id in caches[new_cache_id].videos:
                            best_cache_latency = new_cache_latency

                delta += numrequests * (best_cache_latency - endpoint.caches[cache_id])

        if delta: del_costs.append((delta / videos[video_id], delta, video_id))

    # what if I add an uncached video?
    for video_id in (all_videos - cache.videos):
        delta = 0

        for endpoint_id in cache.endpoints:
            endpoint = endpoints[endpoint_id]
            numrequests = endpoint.requests.get(video_id, 0)
            if numrequests and endpoint.caches[cache_id] < current_latency[video_id][endpoint_id]:
                delta += numrequests * (current_latency[video_id][endpoint_id] - endpoint.caches[cache_id])

        if delta: add_benefits.append((delta / videos[video_id], delta, video_id))

    return del_costs, add_benefits


def find_best_choice_per_cache(args):
    cache_id, (del_costs, add_benefits) = args
    del_costs.sort()
    add_benefits.sort(reverse=True)

    best_choice = None
    for _, add_benefit, add_video_id in add_benefits:
        needed_size = videos[add_video_id] - caches[cache_id].remaining
        tot_del_set, tot_del_cost, tot_del_size = set(), 0, 0
        for _, del_cost, del_video_id in del_costs:
            if del_cost > add_benefit: continue
            tot_del_set.add(del_video_id)
            tot_del_cost += del_cost
            tot_del_size += videos[del_video_id]

            if tot_del_cost > add_benefit: break
            if tot_del_size >= needed_size:
                if not best_choice or (add_benefit - tot_del_cost) > best_choice[0]:
                    best_choice = (add_benefit - tot_del_cost, cache_id, add_video_id, tot_del_set)
                break

    return best_choice

pool = Pool(8, init_worker)

def find_best_choices():
    sys.stderr.write("computing current_latencies\n")
    current_latency = pool.map(compute_latencies, range(nvideos))
    sys.stderr.write("computing deltas\n")
    deltas = map(compute_delta_per_cache, [(current_latency, id) for id in xrange(ncaches)])
    sys.stderr.write("computing best_choices\n")
    best_choices = filter(None, pool.map(find_best_choice_per_cache, enumerate(deltas)))
    best_choices.sort(reverse=True)

    touched_videos = set()
    for benefit, cache_id, video_id, del_set in best_choices:
        if (video_id in touched_videos) or (del_set & touched_videos): continue
        touched_videos.add(video_id)
        touched_videos |= del_set
        yield (benefit, cache_id, video_id, del_set)

total_benefit = 0
try:
    while True:
        found = False
        for best_choice in find_best_choices():
            found = True
            benefit, cache_id, video_id, del_set = best_choice
            cache = caches[cache_id]

            for del_video_id in del_set:
                cache.videos.remove(del_video_id)
                cache.remaining += videos[del_video_id]

            cache.videos.add(video_id)
            cache.remaining -= videos[video_id]
            sys.stderr.write('cache remaining: %d\n' % cache.remaining)
            assert cache.remaining >= 0

            benefit = ((1000.0 * benefit) / totrequests)
            total_benefit += benefit
            sys.stderr.write('cache %d: del %s, add %d\n' % (cache_id, del_set, video_id))
            sys.stderr.write('benefit: %d\n' % benefit)
            sys.stderr.write('total benefit: %d\n' % total_benefit)

        if not found: break
except KeyboardInterrupt:
    pool.terminate()
    pool.join()


used_caches = sum(1 for cache in caches if cache.videos)
print used_caches

for cache_id, cache in enumerate(caches):
    if cache.videos:
        print cache_id, ' '.join(map(str, cache.videos))
