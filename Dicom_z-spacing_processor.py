from scipy import io
import os
import sys
import glob
from pydicom import dcmread
import numpy as np
import SimpleITK as sitk
import shutil

args = sys.argv

if len(args) != 4:
    print("Require 3 parameters: [Source dicom] [spacing mat file] [output folder]")
    sys.exit(-1)

dicom_input_dir = args[1]
spacing_mat_file_path = args[2]
output_folder_path = args[3]

dicom_file_path_list =  glob.glob(dicom_input_dir+"\\*", recursive=False)
print("Found "+str(len(dicom_file_path_list))+" dicom files")

mat_file = io.loadmat(spacing_mat_file_path)
keys = list(mat_file.keys())
print("Using \""+keys[-1]+"\" to extract information from mat.")

items = mat_file[keys[-1]]
slice_location_list = items[-1]
print("Found " + str(len(slice_location_list)) + " slice Z-location data")

slice_thick_list = []
for i in range(0, len(slice_location_list)):
    if i+1 == len(slice_location_list):
        slice_thick_list.append(round(slice_thick_list[0], 3))
    else:
        current_location = slice_location_list[i]
        next_location = slice_location_list[i+1]
        z_spacing = abs(current_location - next_location)
        slice_thick_list.append(round(z_spacing, 3))
print("Calcualted "+str(len(slice_thick_list))+" z-spacing")
print(slice_thick_list[-2])
slice_think_grouped = []
previous_thinkness = 0
group = []
numOfElementsInGroup = []

for i in range(0, len(slice_thick_list)):
    
    if i == 0:
        previous_thinkness = slice_thick_list[0]
    if previous_thinkness == slice_thick_list[i]:
        group.append(slice_thick_list[i])
    else:
        previous_thinkness = slice_thick_list[i]
        slice_think_grouped.append(group)
        numOfElementsInGroup.append(len(group))
        group = []
        group.append(slice_thick_list[i])
    if i == len(slice_thick_list)-1 and previous_thinkness == slice_thick_list[i]:
        slice_think_grouped.append(group)
        numOfElementsInGroup.append(len(group))
print("Found",len(slice_think_grouped), "grouped spacing.")
min_spacing = 999
for spacing in slice_think_grouped:
    if (len(spacing) > 10):
        min_spacing = min(min_spacing, spacing[0])
print("Found min spacing", min_spacing)

print("Start processing slice think in dicom files...")
temp_output_path = os.path.join(output_folder_path, "tmp")
if os.path.exists(temp_output_path):
    shutil.rmtree(temp_output_path)
os.mkdir(temp_output_path)
output_file_list = []
dicom_file_path_list.sort()

k = 0
numOfFileInGroup = numOfElementsInGroup[k]
temp_output_path2 = os.path.join(temp_output_path, str(k))
os.mkdir(temp_output_path2)
new_folder_paths = []
new_folder_paths.append(temp_output_path2)
for i in range(0, len(dicom_file_path_list)):
    if i+1 > numOfFileInGroup:
        file_path = dicom_file_path_list[i]
        file_name = file_path.split('\\')[-1]
        print("Processing "+file_name+"...")
        dcm_file = dcmread(file_path)
        to_be_slice_think = slice_thick_list[i]
        dcm_file.SliceThickness = str(to_be_slice_think)
        new_file_path = os.path.join(temp_output_path2, file_name)
        dcm_file.save_as(new_file_path)
        output_file_list.append(new_file_path)
        k = k + 1
        temp_output_path2 = os.path.join(temp_output_path, str(k))
        os.mkdir(temp_output_path2)
        new_folder_paths.append(temp_output_path2)
        numOfFileInGroup = numOfFileInGroup + numOfElementsInGroup[k]
    file_path = dicom_file_path_list[i]
    file_name = file_path.split('\\')[-1]
    print("Processing "+file_name+"...")
    dcm_file = dcmread(file_path)
    to_be_slice_think = slice_thick_list[i]
    dcm_file.SliceThickness = str(to_be_slice_think)
    new_file_path = os.path.join(temp_output_path2, file_name)
    dcm_file.save_as(new_file_path)
    output_file_list.append(new_file_path)
print("Finished processing DICOM files. saved in "+temp_output_path)

print("Starting second process.")
groupNumber = 0
image_list = []
for new_input_folder in new_folder_paths:
    print("\n\n\nProcessing group",groupNumber,"...")
    reader = sitk.ImageSeriesReader()
    dicom_names = reader.GetGDCMSeriesFileNames(new_input_folder)
    reader.SetFileNames(dicom_names)
    
    image = reader.Execute()

    size = image.GetSize()
    print("Image original size:", size[0], size[1], size[2])
    spacing = image.GetSpacing()
    print("Image original spacing:" , spacing[0], spacing[1], spacing[2])


    resample = sitk.ResampleImageFilter()
    resample.SetInterpolator(sitk.sitkLinear)
    resample.SetOutputDirection(image.GetDirection())
    resample.SetOutputOrigin(image.GetOrigin())
    print("Image target new origin:", image.GetOrigin())
    new_spacing = [spacing[0], spacing[1], min_spacing]
    resample.SetOutputSpacing(new_spacing)
    print("Image target new spacing: ", new_spacing)

    orig_size = np.array(image.GetSize())
    orig_spacing = image.GetSpacing()
    new_z = np.ceil(orig_spacing[2]/min_spacing* orig_size[2])
    should_be_z = np.ceil(orig_spacing[2]/min_spacing* numOfElementsInGroup[groupNumber])
    new_size = [int(orig_size[0]), int(orig_size[1]), int(new_z)]
    should_be_size = [int(orig_size[0]), int(orig_size[1]), int(should_be_z)]
    delta = should_be_z - new_z
    print("Image new size:", should_be_size)
    resample.SetSize(new_size)

    print("Processing resampling...")
    resampledImg = resample.Execute(image) 
    resampledImg = resampledImg[0:should_be_size[0],0:should_be_size[1],0:should_be_size[2]]

    image_list.append(resampledImg)
    writer = sitk.ImageFileWriter()
    writer.SetFileName(os.path.join(output_folder_path,"resampled-"+str(groupNumber)+".nii.gz"))
    writer.Execute(resampledImg)
    print("Group", groupNumber, "Process finished.")
    groupNumber = groupNumber+1
if os.path.exists(temp_output_path):
    shutil.rmtree(temp_output_path)

print("Saved!. Finishing script...")
sys.exit(0)

