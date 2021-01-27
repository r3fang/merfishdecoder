# python merfishdecoder_add_dendrites_name.py 20200303_hMTG_V11_4000gene_best_sample/data 
# python merfishdecoder_add_dendrites_name.py 20200430_hMTG_best_sample_V11_4000gene/data 
# python merfishdecoder_add_dendrites_name.py 20200615_hMTG_4000gene_best_sample/data 
# python merfishdecoder_add_dendrites_name.py 20200818_STG_H1/data 
# python merfishdecoder_add_dendrites_name.py 20201003_STG_4000gene_V11/data 

python merfishdecoder_barcode_assignment.py 20200303_hMTG_V11_4000gene_best_sample/data filteredBarcodes/barcodes.h5 exportedFeatures/dendrite.shp assignedBarcodes/barcodes_dendrite.h5 10 &
python merfishdecoder_barcode_assignment.py 20200430_hMTG_best_sample_V11_4000gene/data filteredBarcodes/barcodes.h5 exportedFeatures/dendrite.shp assignedBarcodes/barcodes_dendrite.h5 10 &
python merfishdecoder_barcode_assignment.py 20200615_hMTG_4000gene_best_sample/data filteredBarcodes/barcodes.h5 exportedFeatures/dendrite.shp assignedBarcodes/barcodes_dendrite.h5 10     &
python merfishdecoder_barcode_assignment.py 20200818_STG_H1/data filteredBarcodes/barcodes.h5 exportedFeatures/dendrite.shp assignedBarcodes/barcodes_dendrite.h5 10                        &
python merfishdecoder_barcode_assignment.py 20201003_STG_4000gene_V11/data filteredBarcodes/barcodes.h5 exportedFeatures/dendrite.shp assignedBarcodes/barcodes_dendrite.h5 10              &
