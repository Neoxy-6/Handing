import time

def now_ms() -> int:
    """return monotonic time in ms"""
    return time.perf_counter_ns() // 1e6
