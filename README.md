# UCC CS2056: Operating Systems

These two labs both simulate low-level OS features. There is a scheduler and a memory manager.


## Scheduler
The Scheduler tracks processes by time quanta. You can add processes (which optionally block for I/O) and then run the scheduler for a specified time interval.

The algorithm itself is a multilevel priority queue. Each queue is assigned a time slice. Lower priority queues are given longer time slices but are only executed after higher priority queues finish execution. Processes are assigned an initial queue and are dropped to lower queues if they fail to complete execution in their alloted time. 

The I/O queue holds processes which need to wait for an external I/O operation. To simulate an async I/O mechanism, the tester code decides when I/O blocking is complete, allowing the process to move back to the main queues.

## Memory Manager

The memory manager simulates a kernel's memory allocation and algorithm. The code is set up to simulate adressing 4MiB of memory with 4KiB pages organized into blocks of exponentially increasing size. The memory manager uses a Next Fit allocation scheme, meaning that the manager keeps track of the most recently allocated block. When a process requests memory be allocated to it, the manager searches the blocks round-robin beginning at the most recently allocated block. This helps reduce the search time for each allocation with the trade-off that the allocated block might not be the smallest possible size. Blocks are represented by a circular linked list to facilitate the Next Fit scheme.

There is a swap mechanism which moves older blocks to the swap space (which would be the disk in a real implementation). Blocks are swapped based on their position in a FIFO queue.Swapping begins after 80% of the blocks have been allocated. Note that's 80% of blocks, not 80% of pages; blocks are a more useful metric here because we're likely to run out of large blocks before we run out of memory.

There's also some basic tester code in the same file.
