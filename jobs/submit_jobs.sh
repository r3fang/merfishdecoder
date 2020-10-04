#! /bin/bash
conda activate md_env

DATA_SET_NAME=20200303_hMTG_V11_4000gene_best_sample/data
DATA_HOME=gc://r3fang/MERFISH_raw_data
ANALYSIS_HOME=/mnt/NAS/Fang/Analysis/MERFISH/merfish_analysis
MERFISH_DECODER=/home/rfang/github/merfishdecoder/bin/merfishdecoder

# create analysis
python $MERFISH_DECODER create-analysis \
	--data-set-name=${DATA_SET_NAME} \
	--codebook-name=hMTGE1_V11_codebook_4000.csv \
	--data-organization-name=hMTGdataorganization_48bit_6z.v11.csv \
	--microscope-parameter-name=MERFISH_MZ.json \
	--microscope-chromatic-aberration-name=MERFIFH_MZ_ca_profile_2020_10_01_.pkl \
	--position-name=20200303_hMTG_V11_4000gene_best_sample_positions.csv


