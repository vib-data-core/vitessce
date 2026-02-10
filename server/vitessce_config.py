# now create the config
spot_size_micron = 120
umap_radius = 3

import numpy as np
from vitessce import (
    VitessceConfig,
    Component as cm,
    CoordinationType as ct,
    CoordinationLevel as CL,
    AnnDataWrapper,
    ImageOmeZarrWrapper,
)

from vitessce import hconcat, vconcat

vc = VitessceConfig(
    schema_version="1.0.18",
    name="Benchmark",
    description="Visium HD",
    base_dir=BASE_DIR,
)

# get the center of the tissue
xy = adata.obsm["spatial"]
center_x = float(np.mean(xy[:, 0]))
center_y = float(np.mean(xy[:, 1]))

spatial_zoom, spatial_target_x, spatial_target_y = vc.add_coordination(
    ct.SPATIAL_ZOOM,
    ct.SPATIAL_TARGET_X,
    ct.SPATIAL_TARGET_Y,
)

spatial_zoom.set_value(-4)
spatial_target_x.set_value(center_x)
spatial_target_y.set_value(center_y)

# --- Dataset & files ---------------------------------------------------------
dataset = vc.add_dataset(name="Liver dataset").add_object(
    ImageOmeZarrWrapper(
        img_path=os.path.basename(path_img),
        coordination_values={"fileUid": "img1"},
    )
)

dataset.add_object(
    AnnDataWrapper(
        adata_path=os.path.basename(path_adata),
        obs_feature_matrix_path="X",
        obs_spots_path="obsm/spatial",
        obs_set_paths=["obs/leiden_1"],
        # obs_feature_column_paths=["obs/total_counts"],
        obs_set_names=["Leiden"],  # <-- optional, display name in UI
        obs_embedding_paths=["obsm/X_umap"],
        obs_embedding_names=["UMAP"],
        coordination_values={
            "obsType": "spot",
            "featureType": "gene",
            "featureValueType": "expression",
        },
    )
)

# QC / obs features
dataset.add_object(
    AnnDataWrapper(
        adata_path=os.path.basename(path_adata),
        obs_feature_matrix_path=None,
        obs_feature_column_paths=[
            "obs/total_counts",
            "obs/n_genes_by_counts",
            "obs/total_counts_mt",
            "obs/pct_counts_mt",
        ],
        coordination_values={
            "obsType": "spot",
            "featureType": "qc",
            "featureValueType": "value",
        },
    )
)

# --- Views -------------------------------------------------------------------
spatial_plot = vc.add_view("spatialBeta", dataset=dataset)
spatial_plot.set_props(title="Leiden Clusters + Gene Expression")

layer_controller = vc.add_view("layerControllerBeta", dataset=dataset)

genes = vc.add_view(cm.FEATURE_LIST, dataset=dataset)
cell_sets = vc.add_view(cm.OBS_SETS, dataset=dataset)
umap = vc.add_view(cm.SCATTERPLOT, dataset=dataset, mapping="UMAP")

# heatmap = vc.add_view(cm.HEATMAP, dataset=dataset)


# histogram for qc
histogram = vc.add_view(cm.FEATURE_VALUE_HISTOGRAM, dataset=dataset)

emb_radius_mode, emb_radius = vc.add_coordination(
    ct.EMBEDDING_OBS_RADIUS_MODE,
    ct.EMBEDDING_OBS_RADIUS,
)
# Manual sizing, and choose your radius:
emb_radius_mode.set_value("manual")  # or "auto"
emb_radius.set_value(umap_radius)

# status_view = vc.add_view(cm.STATUS, dataset=dataset)
# Histogram view
# histogram         = vc.add_view(cm.FEATURE_VALUE_HISTOGRAM, dataset=dataset)

# --- 1. Single-level coordination (obs / feature / coloring) -----------------

# GENES
obs_type, feat_type, feat_val_type, obs_color, feat_sel, obs_set_sel = (
    vc.add_coordination(
        ct.OBS_TYPE,
        ct.FEATURE_TYPE,
        ct.FEATURE_VALUE_TYPE,
        ct.OBS_COLOR_ENCODING,
        ct.FEATURE_SELECTION,
        ct.OBS_SET_SELECTION,
    )
)

# # TEST for lasso does not work
# obs_selection = vc.add_coordination(ct.OBS_SET_SELECTION)

obs_type.set_value("spot")
feat_type.set_value("gene")
feat_val_type.set_value("expression")

# Color by Leiden (cell sets), not by gene selection
obs_color.set_value("cellSetSelection")  # <-- KEY CHANGE
feat_sel.set_value(["CR2"])  # still available if you switch back

obs_set_sel.set_value(None)

# QC view (spatial only; not linked to UMAP)
spatial_qc = vc.add_view("spatialBeta", dataset=dataset)
spatial_qc.set_props(title="QC")
qc_list = vc.add_view(cm.FEATURE_LIST, dataset=dataset)
qc_list.set_props(title="QC list")

# QC coordination
obs_color_qc, feat_type_qc, feat_val_type_qc, feat_sel_qc, obs_set_sel_qc = (
    vc.add_coordination(
        ct.OBS_COLOR_ENCODING,
        ct.FEATURE_TYPE,
        ct.FEATURE_VALUE_TYPE,
        ct.FEATURE_SELECTION,
        ct.OBS_SET_SELECTION,
    )
)

obs_color_qc.set_value("geneSelection")  # use feature values (for QC)
feat_type_qc.set_value("qc")
feat_val_type_qc.set_value("value")
feat_sel_qc.set_value(["total_counts"])
obs_set_sel_qc.set_value(None)


spatial_qc.use_coordination(
    obs_type, obs_color_qc, feat_sel_qc, feat_type_qc, feat_val_type_qc, obs_set_sel_qc
)
spatial_qc.use_coordination(spatial_zoom, spatial_target_x, spatial_target_y)
qc_list.use_coordination(
    obs_type, obs_color_qc, feat_sel_qc, feat_type_qc, feat_val_type_qc
)

"""
feat_type_qc, feat_val_type_qc, feat_sel_qc = vc.add_coordination(
    ct.FEATURE_TYPE, ct.FEATURE_VALUE_TYPE, ct.FEATURE_SELECTION
)
feat_type_qc.set_value("qc")
feat_val_type_qc.set_value("value")
feat_sel_qc.set_value(["total_counts"])
qc_list.use_coordination(obs_type, feat_type_qc, feat_val_type_qc, feat_sel_qc, obs_color)
"""

# obs_color.set_value("geneSelection")
# feat_sel.set_value(["CR2"])

spatial_plot.use_coordination(
    obs_type, feat_type, feat_val_type, obs_color, feat_sel, obs_set_sel
)
spatial_plot.use_coordination(spatial_zoom, spatial_target_x, spatial_target_y)
genes.use_coordination(obs_type, obs_color, feat_sel)
cell_sets.use_coordination(obs_type, obs_set_sel, obs_color)

histogram.use_coordination(
    obs_type,
    feat_type_qc,
    feat_val_type_qc,
    feat_sel_qc,
)

umap.use_coordination(
    obs_type,
    feat_type,
    feat_val_type,
    obs_color,
    feat_sel,
    obs_set_sel,
    emb_radius_mode,
    emb_radius,
)


# Share lasso / selection between spatial_plot, spatial_qc, and UMAP
# spatial_plot.use_coordination(obs_selection)
# spatial_qc.use_coordination(obs_selection)
# umap.use_coordination(obs_selection)

"""
heatmap.use_coordination(
    obs_type,
    feat_type,
    feat_val_type,
    obs_color,
    feat_sel,
    obs_set_sel,
)

heatmap.use_coordination(
    obs_type,
    feat_type,       # "gene"
    feat_val_type,   # "expression"
    feat_sel,
)
"""

# histogram.use_coordination(obs_type, feat_type, feat_val_type, feat_sel)

vc.link_views_by_dict(
    [spatial_plot, spatial_qc, layer_controller],
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
                    "obsType": obs_type,  # or "spot"
                    "spatialLayerVisible": True,
                    "spatialLayerOpacity": 1.0,
                    "spatialSpotRadius": spot_size_micron // 2,
                    "spatialSpotFilled": True,
                    "spatialSpotStrokeWidth": 1.0,
                    "spatialLayerColor": [255, 255, 255],
                    # NOTE: no obsColorEncoding / featureSelection here!
                    "tooltipsVisible": True,
                    "tooltipCrosshairsVisible": True,
                }
            ]
        ),
    },
)

# maybe decide to put an image layer on it

layer_controller.set_props(disable3d=[], disableChannelsIfRgbDetected=True)
# qc_layer_controller.set_props(disable3d=[], disableChannelsIfRgbDetected=True)

vc.layout(
    hconcat(
        # COLUMN 1: spatial_plot, umap
        vconcat(
            spatial_plot,
            umap,
            split=[8, 4],
        ),
        # COLUMN 2: spatial_qc, histogram
        vconcat(
            spatial_qc,
            histogram,
            split=[8, 4],
        ),
        vconcat(
            layer_controller,
            genes,  # gene_list
            qc_list,
            cell_sets,  # spot_sets
            split=[3, 4, 3, 2],  # 3 + 4 + 2 + 3 = 12
        ),
        # Column widths: left wide, middle wide, right narrow
        split=[5, 5, 2],
    )
)


# probably we also want intensity per leiden cluster. Yes but they are on raw counts...?

# vw = vc.widget()
# vw

# TODO: fix lasso
