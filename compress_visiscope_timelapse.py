"""
Minimalist command line program for compression of VisiScope timelapse data to OME-Zarr.
"""
import argparse
import re
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Sequence
import numpy as np

import dask
import dask.array as da
import imageio.v3 as iio
import numpy as np
import yaml
import zarr
from multiscale_spatial_image import to_multiscale
from ome_zarr.scale import Scaler
from ome_zarr.writer import write_image, write_multiscale
from spatial_image import to_spatial_image
import zarr

def main():
    parser = argparse.ArgumentParser(prog="VisiScope Timelapse to Multiscale-OME-Zarr")
    parser.add_argument("flds", nargs="*")
    parser.add_argument("-o", "--out_fld", type=str)
    args = parser.parse_args()
    sites = _parse_sites_multiple_folders(args.flds)

    _first_site = sites[list(sites.keys())[0]]
    _first_channel = _first_site[list(_first_site.keys())[0]]
    _first_fn = _first_channel[0]
    sample = iio.imread(_first_fn)

    for out_file_name in sites:
        channel_stacks = []
        for channel in sites[out_file_name]:
            fns = sites[out_file_name][channel]
            imgs = []
            for fn in fns:
                print(fn)
                imgs.append(
                    da.from_delayed(
                        dask.delayed(iio.imread)(fn),
                        shape=sample.shape,
                        dtype=sample.dtype,
                    )
                )
            imgs_stacked = np.stack(imgs, axis=0)
            channel_stacks.append(imgs_stacked)
        stacks_combined = np.moveaxis(np.stack(channel_stacks, axis=0), 0, 1)

        out_file_name.mkdir(parents=True)
        store = zarr.open(out_file_name, mode="a")
        scaler = Scaler(method="gaussian", max_layer=5)
        write_image(
            stacks_combined,
            group=store,
            scaler=scaler,
        )

        # stack_si = to_spatial_image(
        #     np.moveaxis(stacks_combined, 0, 1),
        #     dims=("t", "c", "z", "y", "x"),
        #     scale={"t": 1, "z": 3, "y": 0.325, "x": 0.325},
        # )
        # stack_msi = to_multiscale(
        #     stack_si,
        #     scale_factors=[
        #         {"z": 1, "y": 2, "x": 2},
        #         {"z": 1, "y": 2, "x": 2},
        #         {"z": 1, "y": 2, "x": 2},
        #     ],
        #     # method=Methods.DASK_IMAGE_GAUSSIAN,
        # )
        # data = [stack_msi[e].image.data for e in stack_msi]
        # out_file_name.mkdir(parents=True)
        # store = zarr.open(out_file_name, mode="a")
        # write_multiscale(data, store)


def _parse_parameter_file(fn: str) -> dict[str, str]:
    with open(fn) as f:
        params = yaml.load(f, Loader=yaml.FullLoader)
    return params


def _extract_metadata_from_filename(file_name: str) -> dict[str, str]:
    keys = [
        "condition",
        "channel",
        "site",
        "timepoint",
    ]
    pattern = re.compile(
        r"^(?P<condition>.*)_(w\d)?(?P<channel>[^_]+)_(?P<site>s\d+)_(?P<timepoint>t\d+)\.stk$"
    )
    match = pattern.match(file_name)
    metadata = {k: match.group(k) for k in keys}
    # metadata["cycle"] = int(metadata["cycle"]) if metadata["cycle"] else None
    return metadata


def _parse_sites(
    fld: str, out_fld: Path | None = None
) -> tuple[DefaultDict[Path, DefaultDict[str, list[Path]]], Path]:
    sites: DefaultDict[Path, DefaultDict[str, list[Path]]] = defaultdict(
        lambda: defaultdict(list)
    )
    if out_fld is None:
        out_fld = Path(fld).parent / (Path(fld).name + "_compressed")
    for e in sorted(
        list(Path(fld).glob("*.stk")),
        key=lambda x: int(x.as_posix().split("_")[-1][1:-4]),
    ):
        metadata = _extract_metadata_from_filename(e.name)
        name = out_fld / (
            "_".join(
                [
                    metadata["condition"],
                    metadata["site"],
                ]
            )
            + ".zarr"
        )
        channel = metadata["channel"]
        sites[name][channel].append(e)
    return sites, out_fld


def _parse_sites_multiple_folders(
    flds: Sequence[str],
    out_fld: Path | None = None,
) -> DefaultDict[Path, DefaultDict[str, list[Path]]]:
    sites = []
    for fld in flds:
        site, out_fld = _parse_sites(fld, out_fld=out_fld)
        sites.append(site)
    return _merge_multiple_sites(sites)


def _merge_multiple_sites(
    sites: list[DefaultDict[Path, DefaultDict[str, list[Path]]]]
) -> DefaultDict[Path, DefaultDict[str, list[Path]]]:
    merged_sites: DefaultDict[Path, DefaultDict[str, list[Path]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for site_dict in sites:
        for site_path, channel_dict in site_dict.items():
            for channel, path_list in channel_dict.items():
                merged_sites[site_path][channel].extend(path_list)
    return merged_sites


if __name__ == "__main__":
    main()
