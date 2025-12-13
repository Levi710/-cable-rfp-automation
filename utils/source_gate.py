from typing import List
from utils.reachability import can_resolve, should_skip_host, mark_unreachable


def should_skip_source(source_name: str, hosts: List[str]) -> bool:
    """Return True if all provided hosts are currently unreachable per skip-cache/DNS.
    For any host that fails DNS now, mark it unreachable in cache.
    """
    if not hosts:
        return False
    all_bad = True
    for host in hosts:
        # Skip if already in skip-cache
        if should_skip_host(host):
            continue
        # If it resolves now, we can try this source
        if can_resolve(host):
            all_bad = False
        else:
            # Mark unreachable for TTL
            mark_unreachable(host, reason='dns')
    return all_bad
