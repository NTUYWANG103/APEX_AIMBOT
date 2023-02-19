# Introduction
This is a YOLOV7 based APEX assisted targeting software

`Note: This is an educational purposes only software, do not use it for any commercial or illegal purposes, we will not be responsible for any unauthorized usage of this software`

Features:
-
- Models that can differentiate between the enemy and friend
- PID smooth moving
- Separate threads to display recognition results in real time
- Customize personalized settings through config file
- Tensorrt speed up 
- Encrpted onnx and trt model
- Manage users using `http://www.ruikeyz.com/`
# Environment
My envrionment using python3.7
```
git clone https://github.com/NTUYWANG103/APEX_deploy.git
conda create -n apex python=3.7
conda activate apex
pip install pipwin
pipwin install pycuda
pip install -r requirements.txt
```
Copy `cuda11.3 with tenssort` to root dir [Click here to download](`https://entuedu-my.sharepoint.com/:u:/g/personal/ywang103_e_ntu_edu_sg/EWaWbrkGBLNGnCTncM3kaDcB9dSY9Xr7EdvyI7aaOJanoQ?e=Jl7nTg`)

# Export pt to onnx
`python export_to_onnx.py --weights weights/best.pt --grid --end2end --simplify --topk-all 12 --iou-thres 0.65 --conf-thres 0.35 --img-size 640 640`

# Run
`python main.py`


# Package
pyinstaller

`pyinstaller --key lhaksklasbjhklcvb main.py`