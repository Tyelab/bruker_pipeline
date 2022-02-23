import tifffile
import imagecodecs
import dask.array
from pathlib import Path


def tiffs2zarr(filenames, zarrurl, chunksize, **kwargs):
    """Write images from sequence of TIFF files as zarr."""

    def imread(filename):
        # return first image in TIFF file as numpy array
        with open(filename, 'rb') as fh:
            data = fh.read()
        return imagecodecs.tiff_decode(data)

    with tifffile.FileSequence(imread, filenames) as tifs:
        with tifs.aszarr() as store:
            da = dask.array.from_zarr(store)
            chunks = (chunksize,) + da.shape[1:]
            da.rechunk(chunks).to_zarr(zarrurl, **kwargs)


tiff_path = Path("/scratch/20211214_CSC013_plane1_-362.075_raw-121_tiffs")

tiffs2zarr(tiff_path.glob('*Ch2*.tif'), "/scratch/lzvm_zarr", 128)