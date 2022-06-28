# Christophe Golke, Jeremy Delahanty, Deryn LeDuke
# December 2021
# Example function for using Dask to create HDF5 files quickly
# When done on Cheetos from a local file store, it can append
# approx. 45k images to H5 in about 2-3 minutes and compress
# the data losslessly from about 22GB to 12-13GB (dependings 
# on how sparse the data is)

import dask.array
import tifffile
from imagecodecs import tiff_decode
from numcodecs.blosc import Blosc
from pathlib import Path
from time import perf_counter


def tiff2hdf5(
    hdf5file: Path,
    tifffiles: Path,
    dataset_name: str = "2p",
    chunksize: int = 128,
    compression: str = None):
    """
    Write images from TIFF files to chunked dataset in HDF5 file.

    Uses Dask and tifffile for opening many individual tiffs and outputs them
    to a losslessly compressed chunked dataset in parallel. Uses the tiff_decode
    library which operates upon the libtiff C library that releases Python's GIL
    most of the time.
    See https://forum.image.sc/t/store-many-tiffs-into-equal-sized-tiff-stacks-for-hdf5-zarr-chunks-using-ome-tiff-format/61055/10
    for tifffile author Christoph Gohlke for their reasoning/source of thi part of
    the code

    Args:
        hdf5file:
            Output HDF5 file path (ie /scratch/filename.hdf5)
        tifffiles:
            Input directory containing tiffs you want to place into H5
        dataset_name:
            Name that should be assigned to the key mapping the 2-photon dataset
        chunksize:
            Size of chunks that will be used for parallel compression of data before
            writing to H5
        compression:
            What compressor to use from the numcodecs library
    """

    # Define imread function to use with tifffile that relies upon the libtiff
    # C library, which allows for fast decoding of tiff data into arrays that get
    # written in parallel to zarr arrays.
    def imread(filename):
        # return image in TIFF file as numpy array
        with open(filename, 'rb') as fh:
            data = fh.read()
        return tiff_decode(data)

    # The image paths from globbing will be appended into this list.
    # TODO: Have an argument in the function that can receive how many
    # channels are expected for processing data into the H5 datasets
    # and create a dictionary where each channel is a key and each
    # value is it's list of paths something like this maybe:
    # image_paths = {"ch#": sorted([path for path in tifffiles.glob(f"*{key}*.tif")])}
    # Currently the only channel we image from is Channel 2, so that's hardcoded for now,
    # but in the future we will definitely have multiple channels.
    image_paths = [path for path in tifffiles.glob("*Ch2*.tif")]

    # When the list above is generated, the elements of the list will be
    # populated however the os happens to fetch each filename for you. This
    # means that things will be out of order most likely! You could wrap the
    # list comprehension above in sorted() to do the same thing, but
    # maybe writing it this way can help people understand it a little better
    sorted_paths = sorted(image_paths)

    # Now that things are sorted correctly, you can tell tifffile to read in
    # all the tiffs and decode them into a temporary chunked zarr store
    # TODO: It should be possible to basically skip this step by using map_blocks
    # and have the tiffs put into dask arrays at this point, which might end up
    # being faster in the end. But writing to zarr and then going from zarr to
    # dask arrays is quite fast since it all happens in parallel anyways on the
    # small chunks that are specified by default.
    store = tifffile.imread(sorted_paths, imread=imread, aszarr=True)

    # Now that the images have been written to zarr, you can use the magic of
    # dask to create a task graph that includes both the conversion of zarrs
    # into dask.arrays and then output things to an H5 file!
    images = dask.array.from_zarr(store)

    # You can operate on the images dask array object to finally output
    # everything into the HDF5 file that's specified in the input argument
    images.to_hdf5(hdf5file, dataset_name, chunks=chunksize, compressor=Blosc)


if __name__ =="__main__":

    start = perf_counter()
    tiff2hdf5("/scratch/test.hdf5", "/scratch/20211105_CSE020_plane1_-587.325_raw-013_tiffs")
    end = perf_counter()

    print(end - start)