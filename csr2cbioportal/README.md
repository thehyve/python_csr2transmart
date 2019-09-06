# Transform PMC data to cBioPortal staging files

This code runs as part of the Luigi Pipeline. To manually test and debug this code, run it with the following arguments:
```
./pmc_cbio_wrapper.py \
  -c ../test_data/intermediate/csr_transformation_data.tsv \
  -n ../test_data/dropzone/NGS/ \
  -o ../test_data/intermediate/cbioportal_staging_files \
```

By running this code, the test data in `../test_data/intermediate/cbioportal_staging_files` will be updated.

Please note that Python3 with Pandas is required.

This code transforms the following data types:
- Clinical data 
- Mutation data
- CNA Segment data
- CNA Continuous data
- CNA Discrete data

File structure, case lists and meta files will also be also added in the output folder.
