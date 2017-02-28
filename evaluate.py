from collections import defaultdict, namedtuple
from argparse import ArgumentParser
import math
import sys

class Endpoint:
    def __init__(self, *args):
        self.latency, self.caches, self.requests = args

def row(fn, fp=sys.stdin):
    return map(fn, fp.readline().strip().split())

def parse_infile(infile):
    parameters = ['videos', 'endpoints', 'requests', 'caches', 'cache_size']
    params = dict(zip(parameters, row(int, infile)))
    videos = row(int, infile)

    endpoints = {}
    for endpoint_id in xrange(params['endpoints']):
        dc_latency, connected_caches = row(int, infile)
        caches = dict(row(int, infile) for _ in xrange(connected_caches))
        endpoints[endpoint_id] = Endpoint(dc_latency, caches, defaultdict(int))

    params['totrequests'] = 0
    for _ in xrange(params['requests']):
        video_id, endpoint_id, numrequests = row(int, infile)
        endpoints[endpoint_id].requests[video_id] += numrequests
        params['totrequests'] += numrequests

    return params, videos, endpoints

def parse_solution(solution):
    (used_caches,) = row(int, solution)
    return {line[0]: line[1:]
            for _ in xrange(used_caches)
            for line in [row(int, solution)]}

def verify(params, caches, videos):
    for cache_id, cached_videos in caches.iteritems():
        if not 0 <= cache_id < params['caches']:
            raise ValueError('unknown cache %d' % cache_id)

        if sum(videos[id] for id in cached_videos) > params['cache_size']:
            raise ValueError('too much space used for cache %d' % cache_id)

def score(params, endpoints, caches):
    benefit = 0
    for endpoint_id, endpoint in endpoints.iteritems():
        for video_id, numrequests in endpoint.requests.iteritems():
            latency = endpoint.latency
            for cache_id, cache_latency in endpoint.caches.iteritems():
                if video_id in caches[cache_id] and cache_latency < latency:
                    latency = cache_latency
            benefit += (endpoint.latency - latency) * numrequests
    return int(math.floor(1000.0 * benefit / params['totrequests']))

def main():
    parser = ArgumentParser(description="compute score for hashcode 2017")
    parser.add_argument('INFILE', type=file, help="provided input file")
    parser.add_argument('SOLUTION', type=file, help="solution file")
    args = parser.parse_args()

    params, videos, endpoints = parse_infile(args.INFILE)
    caches = parse_solution(args.SOLUTION)

    try:
        verify(params, caches, videos)
        print 'score:', score(params, endpoints, caches)
    except Exception as e:
        print e

if __name__ == '__main__':
    main()
