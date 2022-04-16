#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 13:54:26 2022

@author: Knauth
Student Number: 122101624
"""

import numpy as np
import logging

class Process:
    def __init__(self, pid, quanta_needed, has_io=False):
        self.pid = pid
        self.init_quanta = quanta_needed
        self.rem_quanta = self.init_quanta
        
        self.has_io = has_io
   
    def __str__(self):
        return "[Process {} ({}/{})".format(
            self.pid, int(np.clip(self.rem_quanta, 0, np.inf)), self.init_quanta) \
            + (" (IO)" if self.has_io else "") + "]" 
            # python: it's not dumb if it works
            # np.clip is to avoid ugly negative quanta values
            # int() is to avoid ugly decimal point
    
class Scheduler:
    def __init__(self):
        # Setup queues
        self.queues = [[],[],[],[],[],[],[],[]]
        self.blocked = []
        
        # Define global minimum quantum in ns
        self.time_quantum = 10
        
        # Define priority time slices in ns
        # This could be a list, of course, but a dict is 
        # more future proof if I decide to change the 
        # priority labels.
        # It's still O(1) so no reason not to do it.
        self.priority_time_slices = \
            {0:self.time_quantum*1,
             1:self.time_quantum*2, 
             2:self.time_quantum*4,
             3:self.time_quantum*8,
             4:self.time_quantum*16,
             5:self.time_quantum*32,
             6:self.time_quantum*64,
             7:self.time_quantum*128}
            
        self.current_queue = 0 # current process queue
    
    # Add a process to the specified queue
    # end specifies whether the process goes to the 
    # beginning or end of the new queue
    def add_process(self, proc, pri, end=True):
        if end:
            self.queues[pri].append(proc)
            logging.debug("\t" + str(proc) + " added to end of " + str(pri))
        else:
            self.queues[pri].insert(0, proc)
            logging.debug("\t" + str(proc) + " added to start of " + str(pri))
    
    # Remove a process from the queue
    def end_process(self, proc, q_idx):
        logging.debug("\t" + str(proc) + " ends.")
        self.queues[q_idx].remove(proc)
    
    # Change process priority
    # end specifies whether the process goes to the 
    # beginning or end of the new queue
    def change_priority(self, proc, q_idx, new_idx, end=True):
        logging.debug("\t" + str(proc) + " removed from " + str(q_idx))
        proc_temp = proc
        self.queues[q_idx].remove(proc)
        self.add_process(proc_temp, new_idx, end)
    
    # Move a process to the I/O queue
    # The I/O queue contains tuples of type (index, Process)
    # so that dequeue_io knows where to place the process once
    # it is no longer blocking
    def enqueue_io(self, proc, q_idx):
        self.blocked.append((q_idx, proc))
        self.queues[q_idx].remove(proc)
        
        logging.info("I/O enqueued " + str(proc) + ". Current I/O queue state: ")
        logging.info([str(x[1]) for x in self.blocked]) # only the interesting info in a readable format
        
    
    # Move a process back to the ready queues
    # Processes are moved up by one priority level
    # np.clip is used to avoid index errors 
    # i.e. a process with priority 0 stays at 0
    def dequeue_io(self, idx):
        tup = self.blocked[idx]
        tup[1].has_io = False # no more I/O needed
        self.queues[np.clip(tup[0]-1, 0, 7)].append(tup[1])
        self.blocked.remove(tup)
        
        logging.info("I/O dequeued " + str(tup[1]) + ". Current I/O queue state: ")
        logging.info([str(x[1]) for x in self.blocked]) # only the interesting info in a readable format
    
    # run idle process
    # in reality this would do housekeeping and other tasks
    def idle_process(self):
        logging.info("Running idle process.")
        
    # returns a list of how many tasks are in each queue
    def check_queue_status(self):
        return [len(x) for x in self.queues]
    
    # Process execution logic
    # returns unused time slices
    def exec_process(self, proc, q_idx, time):
        logging.info("Executing " + str(proc) + " with time slice " + str(time) + "ns")
        if proc.has_io:
            logging.info("- Process blocking for I/O, enqueuing.")
            self.enqueue_io(proc, q_idx)
            return time
        
        # Allocate the process its time slice
        proc.rem_quanta -= time
        if proc.rem_quanta <= 0: # process is finished
            logging.info(str(proc) + " completed in " + \
                  str(proc.rem_quanta+time) + "ns")
            self.end_process(proc, q_idx)
            return abs(proc.rem_quanta) # time left over
        elif q_idx == 7: # process is lowest priority, just move to end of queue
            logging.info(str(proc) + \
                  " overran time slice at lowest priority. Moving to end of queue.")
            self.change_priority(proc, q_idx, q_idx, True)
            return 0
        else: # process is not finished, drop to start of next queue
            logging.info(str(proc) + \
                  " overran time slice. Dropping priority.")
            self.change_priority(proc, q_idx, q_idx+1, False)
            return 0
        
    # execute the scheduler for the given amount of time (ns)
    def run(self, sched_time):
        logging.info("Running scheduler for " + str(sched_time) + "ns")
        exec_time = self.priority_time_slices[self.current_queue] # time allocated to exec
        
        # run the scheduler as long as the remaining time is greater than the next 
        # time slice, then cease
        while sched_time > exec_time:
            # examine queue status
            q_states = self.check_queue_status()
            logging.info("Queue statuses: " + str(q_states))
            
            # ignore below
            
            # if there is something in queue 0-6, start execution
            # from the highest priority queue
            # if any([len(x) != 0 for x in q_states[:6]]): 
                # self.current_queue = q_states.index([len(x) != 0 for x in q_states[:6]])
                
            # else: # nothing in queues 0-6, go to final queue
            
            # is a queue nonempty?
            queue_nonempty = [x != 0 for x in q_states]
            
            if not any(queue_nonempty): # if all queues are empty
                logging.info("All queues empty.")
                self.idle_process()
                exec_time = sched_time
                extra_time = 0
                
                # at this point we'll have nothing else to do
                # until the scheduler is reawakened
                # so we just forfeit the remainder of our time
                
            else:
                # find the first nonempty queue
                self.current_queue = queue_nonempty.index(True)
                logging.info("Executing in queue " + str(self.current_queue))
                # all we have to do now is run the process at the desired queue
                # with the correct execution time
                exec_time = self.priority_time_slices[self.current_queue] # time allocated to exec
                extra_time = self.exec_process(self.queues[self.current_queue][0], self.current_queue, exec_time)
            
            sched_time -= (exec_time - extra_time)
            logging.info("Remaining scheduler time: " + str(sched_time) + "ns")
        
        logging.info("Stopping scheduler.")
        
        
        
