#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 22 00:29:20 2022

@author: Knauth
Student Number: 122101624
"""

from lab import Process, Scheduler
import logging

# using logging here for debug/info levels of output
logging.basicConfig(format='%(message)s', level=logging.INFO)

# test code
sch = Scheduler()

# the first six processes, last two have I/O
p1 = Process("one", 4) # the pids are just a string, there mostly for debugging
p2 = Process("two", 24)
p3 = Process("three", 300)
p4 = Process("four", 5000)
p5 = Process("five-log", 623, True)
p6 = Process("six-log", 262, True)

sch.add_process(p1, 0)
sch.add_process(p2, 4)
sch.add_process(p3, 2)
sch.add_process(p4, 0)
sch.add_process(p5, 3)
sch.add_process(p6, 0)

# I have the scheduler set up to run for the amount of nanoseconds passed to it
# this allows us to simulate asynchronus I/O as well as add new processes
# I could also have used asyncio module but that would have been more work

sch.run(500) # enough time to get some I/O blocked and finish some of the processes
sch.dequeue_io(0) # Let's say we finish our first I/O operation

p7 = Process("seven", 800) # adding another two processes as well, why not
sch.add_process(p7, 3)

p8 = Process("eight", 30)
sch.add_process(p8, 6)

sch.run(1500) # run some more
sch.dequeue_io(0) # and finish our second I/O operation

sch.run(10000) # and run long enough to finish up all processes, triggering idle
