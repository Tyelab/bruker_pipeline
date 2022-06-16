import zarr
import dask
import tifffile
import imagecodecs
import dask.config
import dask.array as da
import numpy as np
import matplotlib.pyplot as plt

def imread(filename):
    # return first image in TIFF file as numpy array
    with open(filename, 'rb') as fh:
        data = fh.read()
    return imagecodecs.tiff_decode(data)

def subtract_background(average_artifact, data):

    n_zarrs = data.shape[0]
    out = np.empty((n_zarrs,) + average_artifact.shape)

    for i in range(1, n_zarrs):
        out[i] = np.clip(data[i].astype(np.int32) - background.astype(np.int32), a_min=0, a_max=65535).astype(np.uint16)

    return out

output_file = "/scratch/20211105_CSE20_subtraction/data.zarr"

background_image = "/snlkt/data/specialk/jeremy_testing/AVG_artifact.tif"

background = imread(background_image)

no_subtraction_zarr = da.from_zarr("/scratch/20211105_CSE020_no_subtraction/data.zarr")

results = da.map_blocks(
    subtract_background, background, no_subtraction_zarr, dtype=background.dtype
)

with dask.config.set(scheduler='threads'):  # compare to ``scheduler='processes'``?
    results.to_zarr(output_file)