#!/usr/bin/env python3

import concurrent.futures
import random
import time
import urllib.request
import urllib.error
import threading
from collections import Counter


# =========================================================
# Configuration
# =========================================================

TARGET = "http://logging-p2-alb-1152847628.us-east-1.elb.amazonaws.com"

# How long each stage runs.
STAGE_DURATION = 60

# Print statistics every N seconds.
REPORT_INTERVAL = 10

# HTTP timeout.
REQUEST_TIMEOUT = 10


# =========================================================
# Load stages
#
# workers       = number of concurrent requests
# delay         = artificial latency for successful requests
# error_rate    = probability of deliberately calling /error
# =========================================================

STAGES = [
    {
        "workers": 5,
        "delay": 0.2,
        "error_rate": 0.00,
    },
    {
        "workers": 10,
        "delay": 0.5,
        "error_rate": 0.00,
    },
    {
        "workers": 20,
        "delay": 1.0,
        "error_rate": 0.15,
    },
    {
        "workers": 50,
        "delay": 2.0,
        "error_rate": 0.35,
    },
]


# =========================================================
# Statistics
# =========================================================

lock = threading.Lock()

total_requests = 0

status_codes = Counter()

latencies = []


# =========================================================
# Make a request
# =========================================================

def make_request(delay, error_rate):

    global total_requests

    # -----------------------------------------------------
    # Decide whether this request should deliberately fail.
    #
    # Failed requests go to /error.
    # Successful requests go to /slow.
    # -----------------------------------------------------

    should_error = (
        random.random() < error_rate
    )

    if should_error:

        url = (
            f"{TARGET}/error"
        )

    else:

        url = (
            f"{TARGET}/slow"
            f"?delay={delay}"
        )

    start = time.perf_counter()

    try:

        request = urllib.request.Request(
            url,
            method="GET"
        )

        with urllib.request.urlopen(
            request,
            timeout=REQUEST_TIMEOUT
        ) as response:

            status = response.status

            # Consume response body.
            response.read()

    except urllib.error.HTTPError as exc:

        # urllib treats HTTP 4xx/5xx as exceptions.
        status = exc.code

    except Exception:

        # Connection timeout, connection reset,
        # DNS failure, etc.
        status = "connection_error"

    duration_ms = (
        time.perf_counter() - start
    ) * 1000

    with lock:

        total_requests += 1

        status_codes[status] += 1

        latencies.append(
            duration_ms
        )


# =========================================================
# Calculate statistics
# =========================================================

def calculate_statistics(
    start_request_count
):

    with lock:

        current_latencies = latencies[
            start_request_count:
        ]

        current_status_codes = dict(
            status_codes
        )

    if not current_latencies:

        return {
            "requests": 0,
            "p50": 0,
            "p95": 0,
            "p99": 0,
            "status_codes": {}
        }

    values = sorted(
        current_latencies
    )

    def percentile(percent):

        index = int(
            len(values) * percent
        )

        index = min(
            index,
            len(values) - 1
        )

        return values[index]

    return {
        "requests": len(values),
        "p50": percentile(0.50),
        "p95": percentile(0.95),
        "p99": percentile(0.99),
        "status_codes": current_status_codes,
    }


# =========================================================
# Run a load stage
# =========================================================

def run_stage(
    workers,
    delay,
    error_rate
):

    print()
    print("=" * 65)

    print(
        f"Starting stage"
    )

    print(
        f"Concurrent requests : {workers}"
    )

    print(
        f"Slow endpoint delay  : {delay}s"
    )

    print(
        f"Error probability    : "
        f"{error_rate * 100:.0f}%"
    )

    print("=" * 65)

    stage_start = time.time()

    with lock:

        stage_start_request_count = (
            len(latencies)
        )

    previous_request_count = (
        stage_start_request_count
    )

    previous_time = stage_start

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=workers
    ) as executor:

        while (
            time.time() - stage_start
            < STAGE_DURATION
        ):

            # -------------------------------------------------
            # Submit one batch containing "workers" requests.
            #
            # This gives us a controlled amount of concurrency
            # without generating an uncontrolled request storm.
            # -------------------------------------------------

            futures = [
                executor.submit(
                    make_request,
                    delay,
                    error_rate
                )
                for _ in range(workers)
            ]

            concurrent.futures.wait(
                futures
            )

            now = time.time()

            # -------------------------------------------------
            # Print metrics periodically.
            # -------------------------------------------------

            if (
                now - previous_time
                >= REPORT_INTERVAL
            ):

                statistics = calculate_statistics(
                    previous_request_count
                )

                elapsed = (
                    now - previous_time
                )

                requests_per_second = (
                    statistics["requests"]
                    / elapsed
                )

                print()
                print(
                    f"Workers       : {workers}"
                )

                print(
                    f"Requests/sec  : "
                    f"{requests_per_second:.2f}"
                )

                print(
                    f"P50 latency   : "
                    f"{statistics['p50']:.2f} ms"
                )

                print(
                    f"P95 latency   : "
                    f"{statistics['p95']:.2f} ms"
                )

                print(
                    f"P99 latency   : "
                    f"{statistics['p99']:.2f} ms"
                )

                print(
                    f"Status codes  : "
                    f"{statistics['status_codes']}"
                )

                previous_request_count = (
                    len(latencies)
                )

                previous_time = now


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    print()
    print("=" * 65)
    print("             ALB OBSERVABILITY SIMULATION")
    print("=" * 65)
    print()

    print(
        f"Target: {TARGET}"
    )

    print(
        f"Stage duration: "
        f"{STAGE_DURATION}s"
    )

    print()

    print(
        "The test will gradually increase:"
    )

    print(
        "  requests -> latency -> errors"
    )

    print()

    try:

        for stage in STAGES:

            run_stage(
                workers=stage["workers"],
                delay=stage["delay"],
                error_rate=stage["error_rate"]
            )

            print()
            print(
                "Stage complete."
            )

            print(
                "Moving to next stage..."
            )

            # Small pause between stages so the
            # CloudWatch visualization has a clear
            # separation between load levels.

            time.sleep(5)

    except KeyboardInterrupt:

        print()
        print(
            "Simulation stopped by user."
        )

    print()
    print("=" * 65)
    print("Simulation finished.")
    print("=" * 65)