# Introduction
This is a YOLOV7 based APEX Aimbot
![apex](sample/apex.jpg)
`Note: This is an educational purposes only software, do not use it for any commercial or illegal purposes, we will not be responsible for any unauthorized usage of this software` 

## If you like it, please give me a star, thanks!
[![Stargazers over time](https://starchart.cc/NTUYWANG103/APEX_AIMBOT.svg)](https://starchart.cc/NTUYWANG103/APEX_AIMBOT)

# Features
- Enemy and Friend Differentiation:
The model is equipped with the capability to distinguish between enemies and friends, enabling real-time responsive actions. Whether it's on a military battlefield or in security surveillance, it can automatically identify potential threats and harmless targets, thereby greatly enhancing decision-making speed and accuracy.

- PID Smooth Moving:
Utilizing a Proportional-Integral-Derivative (PID) algorithm, the model ensures smooth and stable movement trajectories. This feature is especially useful in target tracking or precision operations, effectively eliminating jitters caused by operational delays or hardware constraints.

- Real-Time Detection Results Display:
The system displays detection results in real-time through an independent process, allowing users to obtain key information instantly. This not only improves the user experience but also provides timely data support in emergency situations.

- Personalized Settings Through Config File:
Users can personalize the model settings by editing the config file, such as detection sensitivity, alert thresholds, etc., achieving applications that better align with individual or organizational needs.

- TensorRT Speed Up:
With the application of TensorRT technology, the model significantly boosts its running speed and effectively solves the shaking problem, particularly when operating at high speeds.

- Model Encryption:
The system offers encryption services for ONNX and TRT models, ensuring the safety and uniqueness of the model and preventing potential theft and tampering.

- Screenshot Saving During Locking or Detection:
The system automatically saves screenshots when a target is locked or an anomaly is detected. This can be used for subsequent analysis and also for collecting a new dataset that includes both false positives and negatives.

- Image Annotation Using Current Models:
By annotating images using the current models, the speed of data annotation is significantly increased, further boosting the efficiency of model training.

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
```
python utils/anno_imgs.py --data_dir your_dataset_dir --engine_path your_trt_engine_path
```

