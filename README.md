# Install Env
use python3.7
```
git clone https://github.com/NTUYWANG103/APEX_deploy.git
conda create -n apex python=3.7
conda activate apex
pip install pipwin
pipwin install pycuda
pip install -r requirements.txt
```
copy cuda_11.3 to root, download here

`https://entuedu-my.sharepoint.com/:u:/g/personal/ywang103_e_ntu_edu_sg/EWaWbrkGBLNGnCTncM3kaDcB9dSY9Xr7EdvyI7aaOJanoQ?e=Jl7nTg`

# Export onnx
`python export_to_onnx.py --weights weights/best.pt --grid --end2end --simplify --topk-all 12 --iou-thres 0.65 --conf-thres 0.35 --img-size 640 640`

# Run
`python apex.py`

# Task
1. build UI
2. write document
3. test to fix bugs

# Package
pyinstaller

`pyinstaller --key lhaksklasbjhklcvb apex.py`