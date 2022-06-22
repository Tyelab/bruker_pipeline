
import zarr
from skimage import exposure, img_as_ubyte
import dask.array

def downsample_zarr(dataset_path):
    
    original = zarr.open_array(dataset_path)

    da = dask.array.from_zarr(original)

    print(type(da))
    
    print("Loaded into zarr!")
    
    transformed = dask.array.map_blocks(lambda x=da: img_as_ubyte(exposure.rescale_intensity(x)), dtype='uint8')
    
    print("Rescaling complete!")
    
    zarr.save_array("/scratch/data2/2p_uint8.zarr", transformed)
    
    print("Zarr saved!")

if __name__ == "main":
    dataset_path = "/snlkt/data/specialk/data/2p.zarr/2p/"
    
    downsample_zarr(dataset_path)