

'''
from vitessce import (
    VitessceConfig,
    Component as cm,
    CoordinationType as ct,
    CoordinationLevel as CL,
    AnnDataWrapper,
    ImageOmeZarrWrapper,
)

vc = VitessceConfig(schema_version="1.0.18", name="Lung", description="Visium HD")


# center
xy = adata.obsm["spatial"]
center_x = float(np.mean(xy[:, 0]))
center_y = float(np.mean(xy[:, 1]))

spatial_zoom, spatial_target_x, spatial_target_y = vc.add_coordination(
    ct.SPATIAL_ZOOM,
    ct.SPATIAL_TARGET_X,
    ct.SPATIAL_TARGET_Y,
)

spatial_zoom.set_value(-5.5)
spatial_target_x.set_value(center_x)
spatial_target_y.set_value(center_y)

# --- Dataset & files ---------------------------------------------------------
dataset = vc.add_dataset(name="Liver dataset").add_object(
    ImageOmeZarrWrapper(
        img_path=output_path_img,
        coordination_values={"fileUid": "img1"},
    )
)

dataset.add_object(
    AnnDataWrapper(
        adata_path=output_path_adata,
        obs_feature_matrix_path="X",
        obs_spots_path="obsm/spatial",  # your AnnData: obsm['spatial']
        coordination_values={
            "obsType": "spot",
            "featureType": "gene",
            "featureValueType": "expression",
        },
    )
)

# --- Views -------------------------------------------------------------------
spatial_plot = vc.add_view("spatialBeta", dataset=dataset)
layer_controller = vc.add_view("layerControllerBeta", dataset=dataset)
genes = vc.add_view(cm.FEATURE_LIST, dataset=dataset)

# --- 1. Single-level coordination (obs / feature / coloring) -----------------
obs_type, feat_type, feat_val_type, obs_color, feat_sel = vc.add_coordination(
    ct.OBS_TYPE,
    ct.FEATURE_TYPE,
    ct.FEATURE_VALUE_TYPE,
    ct.OBS_COLOR_ENCODING,
    ct.FEATURE_SELECTION,
)

obs_type.set_value("spot")
feat_type.set_value("gene")
feat_val_type.set_value("expression")
obs_color.set_value("geneSelection")
feat_sel.set_value(["CR2"])

spatial_plot.use_coordination(obs_type, feat_type, feat_val_type, obs_color, feat_sel)
spatial_plot.use_coordination(spatial_zoom, spatial_target_x, spatial_target_y)
genes.use_coordination(obs_type, obs_color, feat_sel)

# --- 2. Multi-level coordination: imageLayer + spotLayer ----------------------
vc.link_views_by_dict(
    [spatial_plot, layer_controller],
    {
        "imageLayer": CL(
            [
                {
                    "fileUid": "img1",
                    "spatialLayerVisible": True,
                    "spatialLayerOpacity": 1.0,
                    "photometricInterpretation": "RGB",
                }
            ]
        ),
        "spotLayer": CL(
            [
                {
                    # You can pass the coordination scope or just the raw value:
                    "obsType": obs_type,  # or "spot"
                    "spatialLayerVisible": True,
                    "spatialLayerOpacity": 1.0,
                    # <<< THIS IS THE INITIAL SPOT SIZE >>>
                    "spatialSpotRadius": 28.0,
                    "spatialSpotFilled": True,
                    "spatialSpotStrokeWidth": 1.0,
                    "spatialLayerColor": [255, 255, 255],
                    # Hook this layer up to your gene-based coloring:
                    "obsColorEncoding": obs_color,
                    "featureSelection": feat_sel,
                    "featureValueColormap": "plasma",
                    "featureValueColormapRange": [0.0, 1.0],
                }
            ]
        ),
    },
)

layer_controller.set_props(disable3d=[], disableChannelsIfRgbDetected=True)
vc.layout((spatial_plot) | (genes | layer_controller))
vw = vc.widget()
vw


from vitessce import (
    VitessceConfig,
    Component as cm,
    CoordinationType as ct,
    CoordinationLevel as CL,
    AnnDataWrapper,
    ImageOmeZarrWrapper,
)

from vitessce import hconcat, vconcat

vc = VitessceConfig(schema_version="1.0.18", name="Lung", description="Visium HD")

# center
xy = adata.obsm["spatial"]
center_x = float(np.mean(xy[:, 0]))
center_y = float(np.mean(xy[:, 1]))

spatial_zoom, spatial_target_x, spatial_target_y = vc.add_coordination(
    ct.SPATIAL_ZOOM,
    ct.SPATIAL_TARGET_X,
    ct.SPATIAL_TARGET_Y,
)

spatial_zoom.set_value(-5.5)
spatial_target_x.set_value(center_x)
spatial_target_y.set_value(center_y)

# --- Dataset & files ---------------------------------------------------------
dataset = vc.add_dataset(name="Liver dataset").add_object(
    ImageOmeZarrWrapper(
        img_path=output_path_img,
        coordination_values={"fileUid": "img1"},
    )
)

dataset.add_object(
    AnnDataWrapper(
        adata_path=output_path_adata,
        obs_feature_matrix_path="X",
        obs_spots_path="obsm/spatial",  # your AnnData: obsm['spatial']
        coordination_values={
            "obsType": "spot",
            "featureType": "gene",
            "featureValueType": "expression",
        },
    )
)

# --- Views -------------------------------------------------------------------
spatial_plot = vc.add_view("spatialBeta", dataset=dataset)
layer_controller = vc.add_view("layerControllerBeta", dataset=dataset)
genes = vc.add_view(cm.FEATURE_LIST, dataset=dataset)


status_view = vc.add_view(cm.STATUS, dataset=dataset)
# Histogram view
# histogram         = vc.add_view(cm.FEATURE_VALUE_HISTOGRAM, dataset=dataset)

# --- 1. Single-level coordination (obs / feature / coloring) -----------------
obs_type, feat_type, feat_val_type, obs_color, feat_sel = vc.add_coordination(
    ct.OBS_TYPE,
    ct.FEATURE_TYPE,
    ct.FEATURE_VALUE_TYPE,
    ct.OBS_COLOR_ENCODING,
    ct.FEATURE_SELECTION,
)

obs_type.set_value("spot")
feat_type.set_value("gene")
feat_val_type.set_value("expression")
obs_color.set_value("geneSelection")
feat_sel.set_value(["CR2"])

spatial_plot.use_coordination(obs_type, feat_type, feat_val_type, obs_color, feat_sel)
spatial_plot.use_coordination(spatial_zoom, spatial_target_x, spatial_target_y)
genes.use_coordination(obs_type, obs_color, feat_sel)
# histogram.use_coordination(obs_type, feat_type, feat_val_type, feat_sel)

# --- 2. Multi-level coordination: imageLayer + spotLayer ----------------------
vc.link_views_by_dict(
    [spatial_plot, layer_controller],
    {
        "imageLayer": CL(
            [
                {
                    "fileUid": "img1",
                    "spatialLayerVisible": True,
                    "spatialLayerOpacity": 1.0,
                    "photometricInterpretation": "RGB",
                }
            ]
        ),
        "spotLayer": CL(
            [
                {
                    # You can pass the coordination scope or just the raw value:
                    "obsType": obs_type,  # or "spot"
                    "spatialLayerVisible": True,
                    "spatialLayerOpacity": 1.0,
                    # <<< THIS IS THE INITIAL SPOT SIZE >>>
                    "spatialSpotRadius": 28,
                    "spatialSpotFilled": True,
                    "spatialSpotStrokeWidth": 1.0,
                    "spatialLayerColor": [255, 255, 255],
                    # Hook this layer up to your gene-based coloring:
                    "obsColorEncoding": obs_color,
                    "featureSelection": feat_sel,
                    "featureValueColormap": "plasma",
                    "featureValueColormapRange": [0.0, 1.0],
                    # <<< NEW: enable tooltips >>>
                    "tooltipsVisible": True,
                    "tooltipCrosshairsVisible": True,  # optional but nice
                }
            ]
        ),
    },
)

layer_controller.set_props(disable3d=[], disableChannelsIfRgbDetected=True)
# vc.layout(  (spatial_plot) | (  genes | layer_controller  )  )

"""
vc.layout(
    hconcat(
        spatial_plot,
        hconcat(genes, layer_controller, split=[2, 4]),
        split=[6, 6],
    )
)

vc.layout(
    hconcat(
        vconcat(spatial_plot, layer_controller, split=[9, 3]),
        genes,
        split=[9, 3],
    )
)

vc.layout(
    (spatial_plot)
    | (
        (genes | layer_controller)
        / histogram
    )
)

vc.layout(
    hconcat(
        vconcat(spatial_plot, layer_controller, split=[8, 4]),
        genes,
        split=[9, 3],
    )
)
"""

vc.layout((spatial_plot) | ((genes | layer_controller) / status_view))

vw = vc.widget()
vw


import numpy as np
import zarr
from ome_zarr.writer import write_multiscale, write_image
from typing import Literal


def dataarray_to_ome_zarr(
    img_da,
    channel_names,
    output_path,
    img_name="Image",
    chunks=(1, 256, 256),
    channel_colors=None,
    zarr_format: Literal[2, 3] = 2,
):
    """
    Convert an xarray.DataArray (c, y, x) to an OME-Zarr (Zarr v2) multiscale image.

    Parameters
    ----------
    img_da : xarray.DataArray
        DataArray with dimensions ('c', 'y', 'x'). Backed by dask or numpy.
    channel_names : list[str]
        Channel names for omero.channels[].label.
    output_path : str
        Path to the output OME-Zarr store (directory ending in .ome.zarr is typical).
    img_name : str, default "Image"
        Image name for omero.name.
    chunks : tuple[int], default (1, 256, 256)
        Chunk sizes in (c, y, x) order.
    channel_colors : dict[str, str] or None, default None
        Map channel_name -> hex color string (e.g. "FF0000").
        If None, "FFFFFF" is used for all channels.
    """

    # Ensure dims are in (c, y, x) order
    expected_dims = ("c", "y", "x")
    if tuple(img_da.dims) != expected_dims:
        img_da = img_da.transpose(*expected_dims)

    data = img_da.data  # dask or numpy array
    dtype = np.dtype(data.dtype)

    # Int vs float range for default display window
    if dtype.kind in ("u", "i"):
        info = np.iinfo(dtype)
    else:
        info = np.finfo(dtype)

    default_window = {
        "start": 0,
        "min": 0,
        "max": int(info.max),
        "end": int(info.max),
    }

    # Make sure channel metadata matches the data
    n_channels = data.shape[0]
    if len(channel_names) != n_channels:
        raise ValueError(
            f"len(channel_names)={len(channel_names)} does not match "
            f"number of channels in data={n_channels}"
        )

    if channel_colors is None:
        channel_colors = {name: "FFFFFF" for name in channel_names}

    # Zarr v2 store: this is the "v2 vs v3" part.
    # Using DirectoryStore + open_group(mode='w') gives you a Zarr v2 store.
    z_root = zarr.open_group(output_path, mode="w", zarr_format=zarr_format)

    # Write a single-scale (or multiscale, if you pass more arrays) OME-NGFF image
    # The writer will populate the 'multiscales' attribute on z_root.
    write_image(
        image=data,
        group=z_root,
        axes=[
            {"name": "c", "type": "channel"},
            {"name": "y", "type": "space"},
            {"name": "x", "type": "space"},
        ],
        storage_options={"chunks": chunks},
    )
    """
    write_multiscale(
        arrays=[data],
        group=z_root,
        axes=[
            {"name": "c", "type": "channel"},
            {"name": "y", "type": "space"},
            {"name": "x", "type": "space"},
        ],
        storage_options={"chunks": chunks},
    )
    """

    # Add OMERO-style metadata (channel names, colors, window)
    z_root.attrs["omero"] = {
        "name": img_name,
        # This "version" field matches your earlier style; it refers to the
        # OME-OMERO metadata schema version, not Zarr v2/v3.
        "version": "0.3",
        "rdefs": {
            # For multi-channel RGB-like data you might prefer "color";
            # keeping "greyscale" here to mirror your example.
            "model": "greyscale",
        },
        "channels": [
            {
                "label": ch_name,
                "color": channel_colors.get(ch_name, "FFFFFF"),
                "window": default_window,
            }
            for ch_name in channel_names
        ],
    }
'''