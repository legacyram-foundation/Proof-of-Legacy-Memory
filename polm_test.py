#!/usr/bin/env python3

import time
import random
import statistics
import platform
import os

BUFFER_SIZE = 64 * 1024 * 1024
SAMPLES = 10000
ROUNDS = 20000000

memory = bytearray(BUFFER_SIZE)

def latency_test():

    times = []

    index = random.randint(0, BUFFER_SIZE-1)

    for _ in range(SAMPLES):

        start = time.perf_counter_ns()

        value = memory[index]

        end = time.perf_counter_ns()

        times.append(end-start)

        index = (index ^ value * 2654435761) % BUFFER_SIZE

    return statistics.mean(times), statistics.stdev(times)


def workload():

    index = random.randint(0, BUFFER_SIZE-1)

    start = time.time()

    for _ in range(ROUNDS):

        value = memory[index]

        index = (index * 11400714819323198485 + value) % BUFFER_SIZE

    end = time.time()

    return end-start


print("====== PoLM Hardware Test ======")

print("CPU:", platform.processor())
print("Cores:", os.cpu_count())

lat_avg, lat_std = latency_test()

print("Latency Avg:", int(lat_avg), "ns")
print("Latency Std:", int(lat_std))

t = workload()

print("Workload Time:", round(t,2),"s")

score = ROUNDS/t

print("Score:", int(score))
