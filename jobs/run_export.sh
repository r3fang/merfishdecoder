#!/bin/bash
#SBATCH --time=05:00:00
#SBATCH --nodes=1
#SBATCH --mem=5g
#SBATCH --ntasks-per-node=2
#SBATCH --job-name="decoding"
#SBATCH --output=decoding_%a.out
#SBATCH --error=decoding_%a.err

# exit when any command fails
set -e

#source activate md_env
DATASET_NAME=20200303_hMTG_V11_4000gene_best_sample/data
ANALYSIS_PATH=/mnt/NAS/Fang/Analysis/MERFISH/merfish_analysis/${DATASET_NAME}

cd ${ANALYSIS_PATH}
merfishdecoder export-barcodes \
	--data-set-name=${DATASET_NAME} \
	--decoded-barcodes-name ${ANALYSIS_PATH}/decodedBarcodes/* \
	--output-name=${ANALYSIS_PATH}/exportedBarcodes/barcodes.h5

merfishdecoder filter-barcodes \
	--data-set-name=${DATASET_NAME} \
	--exported-barcodes-name=${ANALYSIS_PATH}/exportedBarcodes/barcodes.h5 \
	--output-name=${ANALYSIS_PATH}/filteredBarcodes/barcodes.h5 \
	--fov-num=20 \
	--keep-blank-barcodes=True \
	--mis-identification-rate=0.05 \
	--min-area-size=1

merfishdecoder export-features \
	--data-set-name=${DATASET_NAME} \
	--segmented-features-name ${ANALYSIS_PATH}/segmentedFeatures/fov_*_zpos_*_DAPI \
	--output-name=${ANALYSIS_PATH}/exportedFeatures/DAPI \
	--buffer-size=15 \
	--min-zplane=3 \
	--border-size=80

merfishdecoder export-features \
	--data-set-name=${DATASET_NAME} \
	--segmented-features-name ${ANALYSIS_PATH}/segmentedFeatures/fov_*_zpos_*_polyT \
	--output-name=${ANALYSIS_PATH}/exportedFeatures/polyT \
	--buffer-size=15 \
	--min-zplane=3 \
	--border-size=80

merfishdecoder export-features \
	--data-set-name=${DATASET_NAME} \
	--segmented-features-name ${ANALYSIS_PATH}/segmentedFeatures/fov_*_zpos_*_DAPI \
	--output-name=${ANALYSIS_PATH}/exportedFeatures/DAPI_all \
	--buffer-size=15 \
	--min-zplane=1 \
	--border-size=0

merfishdecoder export-features \
	--data-set-name=${DATASET_NAME} \
	--segmented-features-name ${ANALYSIS_PATH}/segmentedFeatures/fov_*_zpos_*_polyT \
	--output-name=${ANALYSIS_PATH}/exportedFeatures/polyT_all \
	--buffer-size=15 \
	--min-zplane=0 \
	--border-size=0

merfishdecoder assign-barcodes \
	--data-set-name=${DATASET_NAME} \
	--exported-features-name=${ANALYSIS_PATH}/exportedFeatures/polyT \
	--exported-barcodes-name=${ANALYSIS_PATH}/filteredBarcodes/barcodes.h5 \
	--output-name=${ANALYSIS_PATH}/assignedBarcodes/barcodes_polyT.h5 \
	--buffer-size=0 \
	--max-cores=10

merfishdecoder assign-barcodes \
	--data-set-name=${DATASET_NAME} \
	--exported-features-name=${ANALYSIS_PATH}/exportedFeatures/DAPI \
	--exported-barcodes-name=${ANALYSIS_PATH}/filteredBarcodes/barcodes.h5 \
	--output-name=${ANALYSIS_PATH}/assignedBarcodes/barcodes_DAPI.h5 \
	--buffer-size=-0.5 \
	--max-cores=10

merfishdecoder filter-barcodes \
	--data-set-name=${DATASET_NAME} \
	--exported-barcodes-name=${ANALYSIS_PATH}/assignedBarcodes/barcodes_DAPI.h5 \
	--output-name=${ANALYSIS_PATH}/assignedBarcodes/barcodes_DAPI_filtered.h5 \
	--fov-num=20 \
	--keep-blank-barcodes=True \
	--mis-identification-rate=0.05 \
	--min-area-size=1

merfishdecoder filter-barcodes \
	--data-set-name=${DATASET_NAME} \
	--exported-barcodes-name=${ANALYSIS_PATH}/assignedBarcodes/barcodes_polyT.h5 \
	--output-name=${ANALYSIS_PATH}/assignedBarcodes/barcodes_polyT_filtered.h5 \
	--fov-num=20 \
	--keep-blank-barcodes=True \
	--mis-identification-rate=0.05 \
	--min-area-size=1



