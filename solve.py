class Cache:

    def __init__(self, capacity):
        self.remaining = capacity
        self.videos = set()

nvideos, nendpoints, nrequests, ncaches, cachesize = 5, 2, 4, 3, 100
videos = [50, 50, 80, 30, 110]

latencies = [1000, 500]
endpoints = [{0: 100, 2: 200, 1: 300},
             {}]

requests = {(3, 0): 1500, (0, 1): 1000, (4, 0): 500, (1, 0): 1000}

caches = [Cache(cachesize) for _ in xrange(ncaches)]

def solve():
    best_benefit = float('-inf')
    best_video = None
    best_cache = None

    for video_id, video_size in enumerate(videos):

        for cache_id, cache in enumerate(caches):
            if video_size > cache.remaining: continue
            overall_benefit = 0

            for endpoint_id, endpoint in enumerate(endpoints):
                try:    # not this video in that endpoint
                    nrequest = requests[(video_id, endpoint_id)]    # the try
                    current_latency = latencies[endpoint_id]    # datacenter -> endpoint

                    for connected_cache_id, connected_cache_latency in endpoint.iteritems():
                        if video_id in caches[connected_cache_id].videos:
                            current_latency = min(current_latency, connected_cache_latency)

                    latency = endpoint[cache_id]

                    if latency < current_latency:
                        # punto da tarare
                        latency_benefit = (current_latency - latency) * nrequest
                        overall_benefit += latency_benefit

                except KeyError:
                    pass

            overall_benefit_density = overall_benefit / float(video_size)
            if overall_benefit_density > best_benefit:
                best_benefit = overall_benefit_density
                best_cache = cache_id
                best_video = video_id

    return best_benefit, best_cache, best_video


while True:
    benefit, cache_id, video_id = solve()
    if benefit == 0: break
    #print benefit

    cache = caches[cache_id]
    cache.videos.add(video_id)
    cache.remaining -= videos[video_id]
    #print 'cache_id %d, video_id: %d' % (cache_id, video_id)

used_caches = sum(1 for cache in caches if cache.videos)
print used_caches

for cache_id, cache in enumerate(caches):
    if cache.videos:
        print cache_id, ' '.join(map(str, cache.videos))
