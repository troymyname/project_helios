# ----// HEADER // -------------------------------------------------------------
# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# REFERENCES:
# [1]
# ------------------------------------------------------------------------------

# import dependencies
import sys
sys.path.append("..")

from queue import Queue, LifoQueue


def w2_createQueue(
        lifo_type = False, 
        max_size_int = int(1e6)
    ):
    """
        description:
            Creates a new FIFO or LIFO queue object with an optional maximum size.
        args:
            lifo_type: bool, default False
                Whether to create a LIFO queue instead of a standard FIFO queue.
            max_size_int: int, default 1000000
                Maximum number of items the queue can hold.
        returns:
            queue.Queue or queue.LifoQueue
                The created queue instance.
    """
    if lifo_type:
        container_que = LifoQueue(maxsize = max_size_int)
    else:
        container_que = Queue(maxsize = max_size_int)
    return container_que


def w2_putInQueue(
        obj,
        container_que = None,
        lifo_type = False,
        max_size_int = int(1e6)
    ):
    """
        description:
            Adds an object to an existing queue, or creates a new queue if none is provided.
        args:
            obj: object
                The item to insert into the queue.
            container_que: queue.Queue or queue.LifoQueue, default None
                Existing queue to append to. A new queue is created if omitted.
            lifo_type: bool, default False
                Whether a new queue should be a LIFO queue if one is created.
            max_size_int: int, default 1000000
                Maximum size for a newly created queue.
        returns:
            queue.Queue or queue.LifoQueue
                The queue containing the inserted object.
    """
    if container_que is None:
        # generate new queue object
        if lifo_type:
            container_que = LifoQueue(maxsize = max_size_int)
        else:
            container_que = Queue(maxsize = max_size_int)
        container_que.put(obj)
    else:
        container_que.put(obj)
    return container_que


def w2_getFromQueue(container_que):
    """
        description:
            Removes and returns the next object from a queue using the queue's standard retrieval semantics.
        args:
            container_que: queue.Queue or queue.LifoQueue
                Queue to read from.
        returns:
            object
                The dequeued object.
    """
    obj = container_que.get()
    return obj


def w2_MoveElementsToNewQueue(
        old_container_que,
        new_container_que = None,
        new_que_lifo_type = False,
        new_que_max_size_int = int(1e6)
    ):
    """
        description:
            Transfers all items from one queue into a new or existing queue.
        args:
            old_container_que: queue.Queue or queue.LifoQueue
                Source queue whose contents should be moved.
            new_container_que: queue.Queue or queue.LifoQueue, default None
                Destination queue. A new queue is created if omitted.
            new_que_lifo_type: bool, default False
                Whether the destination queue should be a LIFO queue when created.
            new_que_max_size_int: int, default 1000000
                Maximum size for a newly created destination queue.
        returns:
            tuple
                A pair containing the emptied source queue and the populated destination queue.
    """
    # create new container queue
    if new_container_que is None:
        new_container_que = w2_createQueue(
            lifo_type = new_que_lifo_type,
            max_size_int = new_que_max_size_int
        )
    # transfer to new queue
    while old_container_que.qsize() > 0:
        # get object from old queue
        obj = w2_getFromQueue(
            container_que = old_container_que
        )
        # put object in new queue
        new_container_que = w2_putInQueue(
            obj = obj,
            container_que = new_container_que,
            lifo_type = new_que_lifo_type,
            max_size_int = new_que_max_size_int
        )

    return old_container_que, new_container_que


def w2_emptyQueue(container_que):
    """
        description:
            Removes all items from a queue until it is empty.
        args:
            container_que: queue.Queue or queue.LifoQueue
                Queue to drain.
        returns:
            queue.Queue or queue.LifoQueue
                The emptied queue object.
    """
    while container_que.qsize() > 0:
        _ = container_que.get()
    return container_que


def w2_getQuantityFromQueueIntoList(container_que, quantity_int):
    """
        description:
            Retrieves a fixed number of items from a queue and collects them into a list.
        args:
            container_que: queue.Queue or queue.LifoQueue
                Queue to draw items from.
            quantity_int: int
                Number of items to read from the queue.
        returns:
            tuple
                A pair containing the extracted list and the updated queue.
    """
    # construct a new list
    temp_list = []
    for _ in range(quantity_int):
        temp_list.append(
            w2_getFromQueue(
                container_que = container_que
            )
        )
    return temp_list, container_que


def w2_convertQueueToList(container_que):
    """
        description:
            Drains a queue and returns all remaining items as a Python list.
        args:
            container_que: queue.Queue or queue.LifoQueue
                Queue to convert.
        returns:
            list
                The queue contents in retrieval order.
    """


def w2_convertListToQueue(container_list, lifo_type = False):
    """
        description:
            Builds a queue from a Python list, preserving the iteration order of the items.
        args:
            container_list: list
                Items to enqueue.
            lifo_type: bool, default False
                Whether the resulting queue should be a LIFO queue.
        returns:
            queue.Queue or queue.LifoQueue
                The created queue populated with the provided items.
    """
    # construct a new queue
    container_que = w2_createQueue(lifo_type = lifo_type)
    for item in container_list:
        container_que = w2_putInQueue(
            obj = item,
            container_que = container_que
        )
    return container_que