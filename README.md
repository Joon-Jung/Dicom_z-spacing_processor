# Dicom_z-spacing_processor
A python script to unify the z-spacing of DICOM series with different slice thickness.

# Requirements
* python 3.7
* pydicom
* numpy
* SimpleITK

# Run
`python Dicom_z-spacing_processor.py [Source DICOM] [spacing mat file] [output folder]`

Requires Matlab mat file with a single row of each DICOM file containng Z location.

The script outputs nii.gz files with the same z spacing. Concatenate all nii.gz files with imaging software (e.g., ImageJ) to retrive them as a whole stack of DICOM series.
