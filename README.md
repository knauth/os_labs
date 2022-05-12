# UCC CS2056: Operating Systems

These two labs both simulate low-level OS features. There is a scheduler and a memory manager.


## Scheduler
The Scheduler tracks processes by time quanta. You can add processes (which optionally block for I/O) and then run the scheduler for a specified time interval.

The algorithm itself is a multilevel priority queue. Each queue is assigned a time slice. Lower priority queues are given longer time slices but are only executed after higher priority queues finish execution. Processes are assigned an initial queue and are dropped to lower queues if they fail to complete execution in their alloted time. 

The I/O queue holds processes which need to wait for an external I/O operation. To simulate an async I/O mechanism, the tester code decides when I/O blocking is complete, allowing the process to move back to the main queues.

## Memory Manager

The memory manager simulates 
