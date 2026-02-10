from pathlib import Path
from typing import Mapping, Sequence

import dask.array as da
import numpy as np
import xarray as xr
import zarr
from loguru import logger
from ome_zarr.scale import Scaler
from ome_zarr.writer import write_image, write_multiscale


def xarray_to_ome_zarr(
    tree_or_da: xr.DataArray | xr.DataTree,
    output_path: str | Path,
    channel_names: Sequence[str],
    channel_colors: Mapping[str, str] | None = None,
    chunks: tuple[int, int, int] = (1, 256, 256),
    coords_in_microns: bool = False,
    microns_per_pixel: float = 1.0,  # ignored if coords_in_microns is True (i.e. if True, we fetch the scale factor from the coords)
    scale_factors: Sequence[int]
    | None = None,  # None -> no pyramid, ignored if tree_or_da is tree
    zarr_format: int = 3,
) -> None:
    """
    Write an OME-Zarr image from either a single-resolution DataArray or a
    multi-resolution DataTree.

    For DataTree input, the function writes all `scale*` levels as a multiscale
    pyramid and derives per-level coordinate transforms from the x/y coords.
    For DataArray input, it writes a single scale when `scale_factors` is None,
    or builds a uniform pyramid using `ome_zarr.scale.Scaler` when
    `scale_factors` is provided.

    Parameters
    ----------
    tree_or_da : xarray.DataTree | xarray.DataArray
        Either a DataTree with `scale0`, `scale1`, ... groups containing an
        `image` DataArray, or a single DataArray with dims (c, y, x).
    output_path : str
        Output path to the OME-Zarr store.
    channel_names : list[str]
        Channel labels to store in the OMERO metadata.
    channel_colors : dict[str, str] | None
        Mapping channel name -> hex color string. If None, defaults to white.
    chunks : tuple[int, int, int]
        Zarr chunk sizes in (c, y, x) order.
    coords_in_microns : bool
        If True, x/y coords are assumed to be micrometers already; otherwise
        they are treated as pixels and scaled by `microns_per_pixel`.
    microns_per_pixel : float
        Physical pixel size in micrometers (used when coords_in_microns is False).
    scale_factors : list[int] | None
        Per-level downscale factors for building a pyramid from a DataArray.
        Must be uniform (e.g., [2, 2, 2]). Ignored for DataTree input.
    zarr_format
        Zarr format to write. Ignored if zarr.__version__ < 3.
    """

    def _spacing_from_coords(da):
        dy = (
            float(da.coords["y"][1] - da.coords["y"][0])
            if "y" in da.coords and da.sizes["y"] > 1
            else 1.0
        )
        dx = (
            float(da.coords["x"][1] - da.coords["x"][0])
            if "x" in da.coords and da.sizes["x"] > 1
            else 1.0
        )
        return dy, dx

    try:
        # only supported for zarr version > 2
        z_root = zarr.open_group(output_path, mode="w", zarr_format=zarr_format)
    except TypeError:
        z_root = zarr.open_group(output_path, mode="w")

    axes = [
        {"name": "c", "type": "channel"},
        {"name": "y", "type": "space", "unit": "micrometer"},
        {"name": "x", "type": "space", "unit": "micrometer"},
    ]

    if isinstance(tree_or_da, xr.DataTree):
        tree = tree_or_da
        level_keys = sorted(
            [k for k in tree.keys() if k.startswith("scale")],
            key=lambda k: int(k.replace("scale", "")),
        )

        pyramid = []
        coord_tfm = []

        # If scale_factors provided, ignore them
        if scale_factors is not None:
            logger.warning("scale factors ignored if DataTree")

        for _, key in enumerate(level_keys):
            da = tree[key]["image"].transpose("c", "y", "x")
            pyramid.append(da.data)

            dy, dx = _spacing_from_coords(da)
            if not coords_in_microns:
                dy *= microns_per_pixel
                dx *= microns_per_pixel
            coord_tfm.append([{"type": "scale", "scale": [1.0, float(dy), float(dx)]}])

        write_multiscale(
            pyramid=pyramid,
            group=z_root,
            axes=axes,
            coordinate_transformations=coord_tfm,
            storage_options=[{"chunks": chunks}] * len(pyramid),
        )

    elif isinstance(tree_or_da, xr.DataArray):
        da = tree_or_da.transpose("c", "y", "x")

        dy, dx = _spacing_from_coords(da)
        if not coords_in_microns:
            dy *= microns_per_pixel
            dx *= microns_per_pixel

        if scale_factors is None:
            coord_tfm = [[{"type": "scale", "scale": [1.0, float(dy), float(dx)]}]]
            scaler = None
        else:
            if len(set(scale_factors)) != 1:
                raise ValueError(
                    "Non-uniform scale_factors require precomputed multiscale (DataTree). "
                    "ome_zarr.Scaler only supports a constant downscale."
                )
            downscale = scale_factors[0]
            max_layer = len(scale_factors)
            scaler = Scaler(max_layer=max_layer, downscale=downscale)

            cum = [1.0] + _cum_factors(scale_factors)
            coord_tfm = [
                [{"type": "scale", "scale": [1.0, float(dy * c), float(dx * c)]}]
                for c in cum
            ]

        write_image(
            image=da.data,
            group=z_root,
            axes=axes,
            coordinate_transformations=coord_tfm,
            storage_options={"chunks": chunks},
            scaler=scaler,
        )

    else:
        raise ValueError(
            "tree_or_da must be an xarray.DataTree or xarray.DataArray; "
            f"got {type(tree_or_da).__name__}."
        )

    if channel_colors is None:
        channel_colors = {name: "FFFFFF" for name in channel_names}

    dtype_info = (
        np.iinfo(da.dtype) if da.dtype.kind in ("u", "i") else np.finfo(da.dtype)
    )

    default_window = {
        "start": 0,
        "min": 0,
        "max": dtype_info.max,
        "end": dtype_info.max,
    }

    z_root.attrs["omero"] = {
        "name": "Image",
        "version": "0.3",
        "rdefs": {"model": "color"},
        "channels": [
            {
                "label": ch,
                "color": channel_colors.get(ch, "FFFFFF"),
                "window": default_window,
            }
            for ch in channel_names
        ],
    }


def array_to_ome_zarr(
    img_arr: np.ndarray | da.Array,
    output_path: str | Path,
    channel_names: Sequence[str],
    channel_colors: Mapping[str, str] | None = None,
    chunks: tuple[int, int, int] = (1, 256, 256),
    microns_per_pixel: float = 1.0,
    microns_per_z: float | None = None,
    scale_factors: Sequence[int] | None = None,  # None -> no pyramid
    axes: Sequence[str] = ("c", "y", "x"),
) -> None:
    """
    Write an OME-Zarr image from a numpy/dask array with explicit axes.

    Parameters
    ----------
    img_arr : numpy.ndarray | dask.array.Array
        Image array matching the provided axes.
    output_path : str | Path
        Output path to the OME-Zarr store.
    channel_names : list[str]
        Channel labels to store in the OMERO metadata.
    channel_colors : dict[str, str] | None
        Mapping channel name -> hex color string. If None, defaults to white.
    chunks : tuple[int, int, int]
        Zarr chunk sizes in (c, y, x) order.
    microns_per_pixel : float
        Physical pixel size in micrometers for x/y.
    microns_per_z : float | None
        Physical pixel size in micrometers for z. Defaults to microns_per_pixel.
    scale_factors : list[int] | None
        Per-level downscale factors for building a pyramid. Must be uniform
        (e.g., [2, 2, 2]) if provided.
    axes : Sequence[str] | str
        Axis order as a sequence (e.g., ["c", "y", "x"]) or a string
        (e.g., "cyx" or "czyx").
    """
    if microns_per_z is None:
        microns_per_z = microns_per_pixel

    if isinstance(axes, str):
        axes = list(axes)

    try:
        z_root = zarr.open_group(output_path, mode="w", zarr_format=2)
    except TypeError:
        z_root = zarr.open_group(output_path, mode="w")

    axes_meta = []
    for name in axes:
        if name == "c":
            axes_meta.append({"name": "c", "type": "channel"})
        elif name in {"x", "y", "z"}:
            axes_meta.append({"name": name, "type": "space", "unit": "micrometer"})
        elif name == "t":
            axes_meta.append({"name": "t", "type": "time"})
        else:
            axes_meta.append({"name": name})

    base_scale = []
    for name in axes:
        if name in {"c", "t"}:
            base_scale.append(1.0)
        elif name == "z":
            base_scale.append(float(microns_per_z))
        elif name in {"x", "y"}:
            base_scale.append(float(microns_per_pixel))
        else:
            base_scale.append(1.0)

    if "c" in axes:
        channel_axis = axes.index("c")
        n_channels = img_arr.shape[channel_axis]
        if len(channel_names) != n_channels:
            raise ValueError(
                "channel_names length does not match channel axis size: "
                f"{len(channel_names)} != {n_channels}."
            )
    else:
        if len(channel_names) != 1:
            raise ValueError(
                "No channel axis found in axes; channel_names must have length 1."
            )

    if scale_factors is None:
        coord_tfm = [[{"type": "scale", "scale": base_scale}]]
        scaler = None
    else:
        if len(set(scale_factors)) != 1:
            raise ValueError(
                "Non-uniform scale_factors require precomputed multiscale. "
                "ome_zarr.Scaler only supports a constant downscale."
            )
        downscale = scale_factors[0]
        max_layer = len(scale_factors)
        scaler = Scaler(max_layer=max_layer, downscale=downscale)
        cum = [1.0] + _cum_factors(scale_factors)
        coord_tfm = []
        for c in cum:
            scale = []
            for name, base in zip(axes, base_scale):
                if name in {"x", "y"}:
                    scale.append(float(base * c))
                else:
                    scale.append(float(base))
            coord_tfm.append([{"type": "scale", "scale": scale}])

    write_image(
        image=img_arr,
        group=z_root,
        axes=axes_meta,
        coordinate_transformations=coord_tfm,
        storage_options={"chunks": chunks},
        scaler=scaler,
    )

    if channel_colors is None:
        channel_colors = {name: "FFFFFF" for name in channel_names}

    dtype = np.dtype(img_arr.dtype)
    dtype_info = np.iinfo(dtype) if dtype.kind in ("u", "i") else np.finfo(dtype)

    default_window = {
        "start": 0,
        "min": 0,
        "max": dtype_info.max,
        "end": dtype_info.max,
    }

    z_root.attrs["omero"] = {
        "name": "Image",
        "version": "0.3",
        "rdefs": {"model": "color"},
        "channels": [
            {
                "label": ch,
                "color": channel_colors.get(ch, "FFFFFF"),
                "window": default_window,
            }
            for ch in channel_names
        ],
    }


def _cum_factors(scale_factors: Sequence[int]) -> list[float]:
    out: list[float] = []
    c = 1.0
    for f in scale_factors:
        c *= f
        out.append(c)
    return out
