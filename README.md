# Introduction
This is a YOLOV7 based APEX Aimbot
![apex](sample/apex.jpg)
`Note: This is an educational purposes only software, do not use it for any commercial or illegal purposes, we will not be responsible for any unauthorized usage of this software` 

## If you like it, please give me a star, thanks!
[![Stargazers over time](https://starchart.cc/NTUYWANG103/APEX_AIMBOT.svg)](https://starchart.cc/NTUYWANG103/APEX_AIMBOT)

# Features
- **Enemy and Friend Differentiation:** The model can distinguish between enemies and friends, enhancing decision-making in various scenarios.
  
- **PID Smooth Moving:** Utilizes a PID algorithm for smooth and stable movement trajectories, useful in target tracking and precision operations.

- **Real-Time Detection Results:** Displays detection results in real-time, improving user experience and providing timely data support.

- **Personalized Settings:** Users can edit the config file to customize model settings like detection sensitivity and alert thresholds.

- **TensorRT Speed Up:** Boosts model speed and solves shaking issues, especially at high speeds.

- **Model Encryption:** Offers encryption for ONNX and TRT models to prevent theft and tampering.

- **Screenshot Saving:** Automatically saves screenshots during locking or detection for analysis and dataset collection.

- **Image Annotation:** Speeds up data annotation using current models, enhancing model training efficiency.

# Environment
My envrionment uses python3.7
```
conda create -n apex python=3.7
conda activate apex
pip install pipwin
pipwin install pycuda
pip install -r requirements.txt
```
Install cuda11.8 with tensorrt following the [NVIDIA official instructions](https://docs.nvidia.com/deeplearning/tensorrt/install-guide/index.html)

# Run 
Running for apex (default hold left/right button to auto aim, side button(x2) to auto aim and shoot, side button(x1) to enable and disable the AI:

```
python apex.py
```


You can get the customized settings in `configs/apex.yaml`, set your suitable `smooth` hyperparameter

# Annotate the dataset using current model
This repo [link](https://github.com/NTUYWANG103/SAM-BoudingBox-Refine) refines the bounding box, enhancing the accuracy
```
python utils/anno_imgs.py --data_dir your_dataset_dir --engine_path your_trt_engine_path
```

