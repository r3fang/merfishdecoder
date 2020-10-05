#!/bin/bash
#SBATCH --time=10:00:00
#SBATCH --partition=n1-standard-2
#SBATCH --nodes=1
#SBATCH --mem=7g
#SBATCH --ntasks-per-node=2
#SBATCH --job-name=decoding
#SBATCH --output=decoding_%A_%a.out
#SBATCH --error=decoding_%A_%a.err

# exit when any command fails
set -e
source activate md_env

FOV=${SLURM_ARRAY_TASK_ID}
ZPOSES="1.0,2.0,3.0,4.0,5.0,6.0"
DATASET_NAME=20200303_hMTG_V11_4000gene_best_sample/data
ANALYSIS_PATH=/home/r3fang_g_harvard_edu/merfish_analysis/${DATASET_NAME}
MERFISHDECODER=$HOME/miniconda/envs/md_env/bin/merfishdecoder
MAX_CORES=1

cd ${ANALYSIS_PATH}

IFS=',' read -ra ZPOSLIST <<< "$ZPOSES"
for ZPOS in ${ZPOSLIST[@]}; do
	python $MERFISHDECODER register-images \
		--data-set-name=${DATASET_NAME} \
		--fov=${FOV} \
		--zpos=${ZPOS} \
		--output-name=${ANALYSIS_PATH}/warpedImages/fov_${FOV}_zpos_${ZPOS}.tif \
		--register-drift=True \
		--ref-frame-index=0 \
		--high-pass-filter-sigma=3 \
		--register-color=True \
		--save-fiducials=False \
		> logs/fov_${FOV}_zpos_${ZPOS}.log
done

for ZPOS in ${ZPOSLIST[@]}; do
	python $MERFISHDECODER process-images \
		--data-set-name=${DATASET_NAME} \
		--fov=${FOV}  \
		--zpos=${ZPOS} \
		--warped-images-name=${ANALYSIS_PATH}/warpedImages/fov_${FOV}_zpos_${ZPOS}.tif \
		--output-name=${ANALYSIS_PATH}/processedImages/fov_${FOV}_zpos_${ZPOS}.npz \
		>> logs/fov_${FOV}_zpos_${ZPOS}.log
done

for ZPOS in ${ZPOSLIST[@]}; do
	python $MERFISHDECODER decode-images \
		--data-set-name=${DATASET_NAME} \
		--fov=${FOV} \
		--zpos=${ZPOS} \
		--decoding-images-name=${ANALYSIS_PATH}/processedImages/fov_${FOV}_zpos_${ZPOS}.npz \
		--output-name=${ANALYSIS_PATH}/decodedImages/fov_${FOV}_zpos_${ZPOS}.npz \
		--max-cores=$MAX_CORES \
		--border-size=80 \
		--distance-threshold=0.6 \
		>> logs/fov_${FOV}_zpos_${ZPOS}.log
done

for ZPOS in ${ZPOSLIST[@]}; do
	python $MERFISHDECODER extract-barcodes \
		--data-set-name=${DATASET_NAME} \
		--fov=${FOV} \
		--zpos=${ZPOS} \
		--decoded-images-name=${ANALYSIS_PATH}/decodedImages/fov_${FOV}_zpos_${ZPOS}.npz \
		--output-name=${ANALYSIS_PATH}/decodedBarcodes/fov_${FOV}_zpos_${ZPOS}.h5 \
		--psm-name=${PSM_NAME} \
		--max-cores=$MAX_CORES \
		>> logs/fov_${FOV}_zpos_${ZPOS}.log
done

for ZPOS in ${ZPOSLIST[@]}; do
	python $MERFISHDECODER segmentation \
		--data-set-name=${DATASET_NAME} \
		--fov=$FOV \
		--zpos=$ZPOS \
		--warped-images-name=${ANALYSIS_PATH}/warpedImages/fov_${FOV}_zpos_${ZPOS}.tif \
		--output-name=${ANALYSIS_PATH}/segmentedImages/fov_${FOV}_zpos_${ZPOS}_DAPI.npz \
		--model-type=nuclei \
		--diameter=150 \
		--feature-name=DAPI \
		>> logs/fov_${FOV}_zpos_${ZPOS}.log
done

for ZPOS in ${ZPOSLIST[@]}; do
	python $MERFISHDECODER segmentation \
		--data-set-name=${DATASET_NAME} \
		--fov=$FOV \
		--zpos=$ZPOS \
		--warped-images-name=${ANALYSIS_PATH}/warpedImages/fov_${FOV}_zpos_${ZPOS}.tif \
		--output-name=${ANALYSIS_PATH}/segmentedImages/fov_${FOV}_zpos_${ZPOS}_polyT.npz \
		--model-type=cyto \
		--diameter=200 \
		--feature-name=polyT \
		>> logs/fov_${FOV}_zpos_${ZPOS}.log
done

for ZPOS in ${ZPOSLIST[@]}; do
	python $MERFISHDECODER extract-features \
		--data-set-name=${DATASET_NAME} \
		--fov=${FOV} \
		--zpos=${ZPOS} \
		--segmented-images-name=${ANALYSIS_PATH}/segmentedImages/fov_${FOV}_zpos_${ZPOS}_DAPI.npz \
		--output-name=${ANALYSIS_PATH}/segmentedFeatures/fov_${FOV}_zpos_${ZPOS}_DAPI \
		>> logs/fov_${FOV}_zpos_${ZPOS}.log
done

for ZPOS in ${ZPOSLIST[@]}; do
	python $MERFISHDECODER extract-features \
		--data-set-name=${DATASET_NAME} \
		--fov=${FOV} \
		--zpos=${ZPOS} \
		--segmented-images-name=${ANALYSIS_PATH}/segmentedImages/fov_${FOV}_zpos_${ZPOS}_polyT.npz \
		--output-name=${ANALYSIS_PATH}/segmentedFeatures/fov_${FOV}_zpos_${ZPOS}_polyT \
		>> logs/fov_${FOV}_zpos_${ZPOS}.log
done
