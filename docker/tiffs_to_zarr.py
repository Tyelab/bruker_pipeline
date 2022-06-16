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


tiff_path = Path("/scratch/snlkt_specialk_demo/CSE020/20211105_CSE020_plane1_-587.325_raw-013_tiffs")

tiffs2zarr(sorted(tiff_path.glob('*Ch2*.tif')), "/scratch/20211105_CSE020_no_subtraction/data.zarr", 128)