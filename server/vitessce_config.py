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
