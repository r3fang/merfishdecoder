#!/bin/bash
#SBATCH --time=3:00:00
#SBATCH --nodes=5
#SBATCH --mem=7g
#SBATCH --job-name=train_PSM
#SBATCH --output=train_PSM.out
#SBATCH --error=train_PSM.err

# exit when any command fails
set -e

# activate working environment
source activate md_env

DATASET_NAME=20200303_hMTG_V11_4000gene_best_sample/data
ANALYSIS_PATH=/mnt/NAS/Fang/Analysis/MERFISH/merfish_analysis/${DATASET_NAME}

cd ${ANALYSIS_PATH}

merfishdecoder train-psm \
        --data-set-name=${DATASET_NAME} \
        --decoded-images-name ${ANALYSIS_PATH}/decodedImages/* \
        --output-name=${ANALYSIS_PATH}/pixel_score_machine.pkl \
        --zpos-num=50

