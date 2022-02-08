import h5py
import dask.array
import tifffile
from imagecodecs import tiff_decode


def tiff2hdf5(
    hdf5file, tifffiles, dataset_name='2p', chunksize=128, compression=None
):
    """Write images from TIFF files to chunked dataset in HDF5 file."""

    def imread(filename):
        # return first image in TIFF file as numpy array
        with open(filename, 'rb') as fh:
            data = fh.read()
        return tiff_decode(data)

    store = tifffile.imread(tifffiles, imread=imread, aszarr=True)
    images = dask.array.from_zarr(store)
    print(images)

    with h5py.File(hdf5file, 'w') as hdf:

        dataset = hdf.create_dataset(
            dataset_name,
            shape=images.shape,
            dtype=images.dtype,
            chunks=(chunksize, *images.shape[1:]),
            compression=compression,
        )

        for index in range(0, images.shape[0], chunksize):
            print(index)
            dataset[index : index + chunksize] = images[
                index : index + chunksize
            ]


with tifffile.Timer():
    tiff2hdf5(
        '/scratch/snlkt2p/test.hdf5', '/scratch/snlkt2p/20211105_CSE010_plane1_-355.85_raw-009/*Ch2*.tif', compression='gzip'
    )