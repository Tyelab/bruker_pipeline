import multiprocessing as mp
import numpy as np
import random
import time
import zarr

def create(name):

    print(f'creating sample {name} with process {mp.current_process()}')

    data = np.random.randint(0, 100, size=(300,)*3)

    out = zarr.open(f'zarrs/sample_{name}.zarr', 'a')
    out['data'] = data
    out['data'].attrs['offset'] = [0,]*3
    out['data'].attrs['resolution'] = [1,]*3

if __name__ == '__main__':

    ############ single process (main) ###########

    start = time.time()

    for i in range(10):
        create(i)

    end = time.time()

    print('\n')
    print('single process time: ', end - start)
    print('\n')

    ############ mp.process (all available processes) ###########

    procs = []

    start = time.time()

    for i in range(10):
        proc = mp.Process(target=create, args=(i,))
        procs.append(proc)
        proc.start()

    for proc in procs:
        proc.join()

    end = time.time()

    print('\n')
    print('mp process time: ', end - start)
    print('\n')

    ############ mp.pool example 1 (defined number of processes) ###########

    start = time.time()

    pool = mp.Pool(2)
    pool.map(create, range(10))

    end = time.time()

    print('\n')
    print('mp pool time: ', end - start)
    print('\n')

    ############ mp.pool example 2 (all processes except 1) ###########

    start = time.time()

    total_processes = mp.cpu_count()
    print('Total available processes: ', total_processes)

    pool = mp.Pool(total_processes-1)
    pool.map(create, range(10))

    end = time.time()

    print('\n')
    print('mp pool time: ', end - start)
    print('\n')
