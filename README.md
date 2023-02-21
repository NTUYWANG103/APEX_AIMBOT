# Introduction
This is a YOLOV7 based APEX assisted targeting software

`Note: This is an educational purposes only software, do not use it for any commercial or illegal purposes, we will not be responsible for any unauthorized usage of this software`

Features:
-
- Models that can differentiate between the enemy and friend
- PID smooth moving
- Individual process to display detectrion results in real time
- Customize personalized settings through config file
- Tensorrt speed up (solving the shaking problem when speed is fast)
- Encrypt onnx and trt model
- Manage users using `http://www.ruikeyz.com/`
- Save screenshot while locking or detected -> collect new dataset (false positive and negative)
- Annotate images using current models -> faster annotation
- Package to exe
# Environment
My envrionment uses python3.7
```
git clone hhttps://github.com/NTUYWANG103/APEX_AIM_ASSISTANT.git
conda create -n apex python=3.7
conda activate apex
pip install pipwin
pipwin install pycuda
pip install -r requirements.txt
```
Copy `cuda11.3 with tensorrt` to root dir [Click here to download](`https://entuedu-my.sharepoint.com/:u:/g/personal/ywang103_e_ntu_edu_sg/EWaWbrkGBLNGnCTncM3kaDcB9dSY9Xr7EdvyI7aaOJanoQ?e=Jl7nTg`)

# Export pt to onnx
`python export_to_onnx.py --weights weights/best.pt --grid --end2end --simplify --topk-all 12 --iou-thres 0.65 --conf-thres 0.35 --img-size 640 640`

# Run
`python main.py`

# Annotate the dataset using current model
`python utils/anno_imgs.py --data_dir your_dataset_dir`

# Package
`pyinstaller --key lhaksklasbjhklcvb main.py`

copy `mouse_driver/ghub_mouse.dll` &nbsp; `mouse_driver/msdk.dll` &nbsp; `configs` &nbsp; `weights` &nbsp; `cuda_11.3` to the package directory