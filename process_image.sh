
export file_code=8jzxm24d1k4uydz4

curl https://radar.kit.edu/radar-backend/archives/$file_code/versions/1/content

# Gets 10.35097-8jzxm24d1k4uydz4.tar

# Now we can extract the tar file and process the images as needed.

tar -xvf 10.35097-8jzxm24d1k4uydz4.tar

uv venv --python 3.12 && source .venv/bin/activate && uv pip install eubi-bridge==0.1.2b8

eubi to_zarr 10.35097-8jzxm24d1k4uydz4/data/dataset/*.tif zarr_data --ome_zarr_version 0.5

cp 10.35097-8jzxm24d1k4uydz4/data/descriptive-md/dataset.desc_md.xml zarr_data/27-30.zarr

# Rename to CASENT0744903.zarr, it is in the metadata

mv zarr_data/27-30.zarr zarr_data/CASENT0744903.zarr

python3 desc_to_rocrate.py zarr_data/27-30.zarr/dataset.desc_md.xml zarr_data/27-30.zarr/ro-crate-metadata.json

# (exported manually to HuggingFace https://huggingface.co/buckets/tiagolubiana/antscan/)
