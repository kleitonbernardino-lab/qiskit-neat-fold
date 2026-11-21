import time

def benchmark_richardson_extrapolation():
    scales = [1.0, 1.5, 2.0]
    values = [0.82, 0.74, 0.65]
    start = time.perf_counter()
    # Linear fit simulation
    slope = (values[-1] - values[0]) / (scales[-1] - scales[0])
    intercept = values[0] - slope * scales[0]
    elapsed = time.perf_counter() - start
    return intercept, elapsed

if __name__ == '__main__':
    intercept, duration = benchmark_richardson_extrapolation()
    print(f"Extrapolated zero-noise expectation: {intercept:.4f} in {duration*1e6:.2f} us")
