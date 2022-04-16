#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 13:54:26 2022

@author: June Knauth
Student Number: 122101624
"""

"""
Notes:
All memory values are passed in bytes.
"""

import logging
import copy
import random
import math

# Size of the page in bytes
PAGE_SIZE = 4096

# The block table, in format <page count>:<block quantity>
BLOCK_TABLE = {2:32,
               4:16,
               8:16,
               16:16,
               32:16}

# Total memory size, used for sanity checks
MEMORY_SIZE = 4194304

# Some helpful functions for testing
def KiB_to_B(kib):
    return kib * 1024

def bytes_to_pages(b):
    return b/PAGE_SIZE

class Page():
    def __init__(self):
        self.size = PAGE_SIZE
        self.allocated_size = 0
        # No need to store actual data here, just keep track of how
        # much fake data we have stored

    def __str__(self):
        return f"[Page: {self.allocated_size}/{self.size}B]"

class Block():
    def __init__(self, page_count, next_block):
        # Setup pages
        self.pages = []
        for i in range(page_count):
            self.pages.append(Page())
            
        # Setup next pointer
        self.next = next_block
        
        # Allocated flag
        self.allocated = False
        
        # Total memory size of the block
        self.size = sum([x.size for x in self.pages])
        
        self.num_pages = len(self.pages)
        
        # PID is initialized to None
        self.PID = None
        
    def __str__(self):
        return f"[Block: {len(self.pages)} pages, {'Free' if not self.allocated else 'In Use'}, PID {self.PID}]"
    
    """
    Write the data to the pages and mark block as allocated
    """
    def allocate(self, data_size, pid=None):
        self.allocated = True
        
        num_full_pages = data_size//PAGE_SIZE
        # hellish, but this is only for the simulation
        # we set the state of the full pages to full
        for i in range(num_full_pages):
            self.pages[i].allocated_size = PAGE_SIZE
        
        # then set the state of the remainder
        if data_size % PAGE_SIZE != 0:
            self.pages[num_full_pages].allocated_size = data_size % PAGE_SIZE
        
        # The block stores the pid to which it is allocated
        self.PID = pid
        
        logging.debug(f"Allocated {str(self)} to PID {self.PID}")
    
    """
    Print the status of each page in the block.
    """
    def print_page_status(self):
        status = "Block Status:\n" + \
                 "\n".join([str(j) for j in self.pages])
        logging.info(status)
        
    """
    Deallocate the block.
    """
    def deallocate(self):
        self.allocated = False
        
        for i in self.pages:
            i.allocated_size = 0
            
        logging.debug(f"Freed block which belonged to PID {self.PID}")
        self.PID = None
        
    def get_used_size(self):
        return sum([x.allocated_size for x in self.pages])
            
class MemoryManager():
    def __init__(self, block_table=BLOCK_TABLE):
        # Setup the blocks
        # We iterate backwards through the sizes to create the
        # circular linked list
        blocks_temp = reversed([[x[0]]*x[1] for x in block_table.items()])
        counts = []
        for i in blocks_temp:
            for j in i:
                counts.append(j)
        
        # create the tail first
        # then move backwards and finally link the head to the tail
        tail = Block(counts[0], None)
        last = tail
        for page_ct in counts[1:]:
            cur = Block(page_ct, last)
            last = cur
            
        tail.next = last
        self.head = last
        
        # Total number of blocks
        self.total_block_count = len(counts)
        
        # Total number of pages
        self.total_page_count = sum([x.num_pages for x in self.get_blocks_as_list()])
        
        # Persistent pointer for traversal
        self.cur = self.head
        
        # This won't change so memoize it
        self.max_mem_size = self.get_max_mem_size()

        # Sanity check
        assert self.max_mem_size == MEMORY_SIZE

        # Keep track of this so we know when we need to begin swapping
        self.used_memory = 0
        
        # FIFO queue for swapping
        self.swap_queue = []
    
        # The actual swap location        
        self.swap_disk = []
        
    def __str__(self):
        return f"[MemoryManager: {self.used_memory}/{self.max_mem_size}B, {self.count_active_blocks()}/{self.total_block_count} blocks]"
    
    def get_blocks_as_list(self):
        blocks = []
        cur = self.head
        
        for i in range(self.total_block_count):
            blocks.append(cur)
            cur = cur.next
    
        return blocks
    
    def get_max_mem_size(self):
        return sum([x.size for x in self.get_blocks_as_list()])
    
    def print_blocks(self, active=True): # only print used blocks by default
        if not active:
            logging.info("\n".join([str(i) for i in self.get_blocks_as_list()]))
        else:
            logging.info("\n".join([str(i) for i in filter(lambda x: x.allocated,
                                                           self.get_blocks_as_list())]))
    def count_active_blocks(self):
        return len(list(filter(lambda x: x.allocated, self.get_blocks_as_list())))
    """
    Main allocation logic
    """
    def malloc(self, alloc_size, pid):
        # First we check if we need to swap, and if so do so
        self.check_and_swap()

        # Next fit memory allocation
        start = self.cur # Current location
        # iterate until we come back to the same place
        while self.cur.next != start:
            self.cur = self.cur.next
            if self.cur.size >= alloc_size and not self.cur.allocated: # Is this block large enough and free?
                self.cur.allocate(alloc_size, pid) # Allocate it!
                self.swap_queue += [self.cur] # Add the block to swap queue
                #logging.info(f"apd {str(self.cur)}") # debugging code
                self.used_memory += alloc_size # Add to used mem counter
                
                logging.info(f"Allocated {self.cur}; {self.used_memory}/{self.max_mem_size}B; {self.count_active_blocks()}/{self.total_block_count} blocks")
                return
        
        logging.info("Could not allocate memory!")
        
    """
    Free all memory belonging to a given PID
    """
    def free(self, pid):
         for i in self.get_blocks_as_list():
            if i.PID == pid:
                self.used_memory -= i.get_used_size()
                self.swap_queue.remove(i)
                logging.info(f"Removed {str(i)}; {self.used_memory}/{self.max_mem_size}B; {self.count_active_blocks()}/{self.total_block_count} blocks")
                i.deallocate()
    
    def check_and_swap(self):
        #logging.info("\n".join([str(i) for i in self.swap_queue]))
        if self.count_active_blocks() >= .8*self.total_block_count: # begin swapping at 80% block capacity]
            logging.info("Beginning Swap")
            while self.count_active_blocks() >= .5*self.total_block_count: # swap until below 50%
                toswap = self.swap_queue.pop(0) # Pop first element in FIFO 
                self.swap_disk.append(copy.deepcopy(toswap)) # Move a copy to disk
                self.used_memory -= toswap.get_used_size() # Subtract used memory
                logging.info(f"Swapped {str(toswap)}")
                toswap.deallocate()
            logging.info("Done Swapping")

def main():
    logging.basicConfig(format='%(message)s', level=logging.INFO)

    logging.info("===Running test code===")
    mem = MemoryManager(BLOCK_TABLE)
    logging.info(f"Created {str(mem)}")
    logging.info("===Allocating some memory===")
    mem.malloc(KiB_to_B(3), "A")
    mem.malloc(KiB_to_B(8), "B")
    mem.malloc(KiB_to_B(9), "C")
    mem.malloc(KiB_to_B(36), "D")
    mem.malloc(KiB_to_B(63), "E")
    mem.malloc(KiB_to_B(64), "F")
    logging.info("===Status===")
    logging.info(mem)
    mem.print_blocks()
    logging.info("===Attempting to allocate larger than the largest block===")
    mem.malloc(KiB_to_B(129), "Oops")
    logging.info("===Allocating more memory to test swap===")
    for i in range(75):
        mem.malloc(KiB_to_B(8), "MemHungryProcess")
    mem.malloc(KiB_to_B(3), "G")
    mem.malloc(KiB_to_B(8), "H")
    mem.malloc(KiB_to_B(9), "I")
    mem.malloc(KiB_to_B(36), "J")
    mem.malloc(KiB_to_B(63), "K")
    mem.malloc(KiB_to_B(64), "L")
    logging.info("===Status===")
    logging.info(mem)
    mem.print_blocks()
    logging.info("===Testing free===")
    mem.free("MemHungryProcess")
    logging.info("Freed blocks from MemHungryProcess")
    logging.info("===Status===")
    logging.info(mem)
    mem.print_blocks()
    
    logging.info("===Mashing it all up===")
    for i in range(10):
        mem.malloc(math.floor(KiB_to_B(random.random()*130)), str(i))
    mem.free("I")
    mem.free("K")
    mem.free("L")
    mem.free("5")
    mem.free("G")
    mem.free("8")
    for i in range(11, 21):
        mem.malloc(math.floor(KiB_to_B(random.random()*130)), str(i))
    for i in range(70):
        mem.malloc(math.floor(KiB_to_B(random.random()*13)), str(i))
            

    
if __name__=="__main__":
    main()
    