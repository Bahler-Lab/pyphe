pyphe-quantify timecourse --grid auto_1536 --pattern "images/*.jpg" --s 0.2 --d 2 --out timecourse_quant --timepoints images/timepoints.txt
pyphe-quantify batch --grid auto_1536 --pattern "images/*.jpg" --s 0.2 --d 2 
pyphe-analyse --edt edt.csv --gridnorm standard1536 --load_layouts --check True --rcmedian --format pyphe-quantify-batch
pyphe-interpret --ld pyphe-analyse_data_report.csv --axis_column Strain --grouping_column Plate --control JB22 --set_missing_na --circularity 0.85 
