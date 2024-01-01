# Introduction
This is a YOLOV7 based APEX Aimbot
![apex](sample/apex.jpg)
`Note: This is an educational purposes only software, do not use it for any commercial or illegal purposes, we will not be responsible for any unauthorized usage of this software` 

## If you like it, please give me a star, thanks!
[![Stargazers over time](https://starchart.cc/NTUYWANG103/APEX_AIMBOT.svg)](https://starchart.cc/NTUYWANG103/APEX_AIMBOT)

# Environment
My envrionment uses python 3.7
```
conda create -n apex python=3.7
conda activate apex
pip install pipwin
pipwin install pycuda
pip install -r requirements.txt
```
Install cuda 11.8 with tensorrt following the [NVIDIA official instructions](https://docs.nvidia.com/deeplearning/tensorrt/install-guide/index.html)

# Run 
Running for apex (default hold left/right button to auto aim, side button(x2) to auto aim and shoot, side button(x1) to enable and disable the AI:

```
python apex.py
```


You can get the customized settings in `configs/apex.yaml`, set your suitable `smooth` hyperparameter

# Annotate the dataset using current model
This [repo](https://github.com/NTUYWANG103/SAM-BoudingBox-Refine) refines the bounding box, enhancing the accuracy
```
python utils/anno_imgs.py --data_dir your_dataset_dir --engine_path your_trt_engine_path
```

