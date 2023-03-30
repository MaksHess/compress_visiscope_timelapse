from setuptools import setup

setup(
    name="visiscope_timelapse_to_ome_zarr",
    version="0.1.0",
    py_modules=[
        "compress_visiscope_timelapse",
    ],
    install_requires=[
        "imageio",
        "spatial_image",
        "multiscale_spatial_image",
        "zarr",
        "ome-zarr",
    ],
    author="Max Hess",
    author_email="max.hess@mls.uzh.ch",
)
