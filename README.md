pipeline to convert antscan (https://doi.org/10.1038/s41592-026-03005-0) to OME-Zarr, originaly in CC-BY

goals of the prototype:

- evaluate eubi-bridge and its finetuning for 0.5 as a converter

- evaluate the conversion of the original metadata into a OME-NGFF 2024 Challenge-like RO-Crate (and generally the metadata conversion/load workflow)

- perhaps consider it in the context of https://github.com/AllenNeuralDynamics/bioparquet-sandbox and fits for the scenario

- explore the fit of https://github.com/lubianat/zowser for this workflow; update zowser to support other kinds of metadata. or evolutions of a single-image ro-crate profile. or single-image parquets. or ???.

- explore the use of the thumbnails convention for 3D native metadata (workflows; ome-zarr.js? some other way to max project or volview?)
