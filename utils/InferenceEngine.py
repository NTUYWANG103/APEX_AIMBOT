import os
os.environ["PATH"]+=f";v11.8;v11.8\\bin;v11.8\\lib"
os.environ["CUDA_MODULE_LOADING"]="LAZY"
import numpy as np
import tensorrt as trt
import time
import pycuda.driver as cuda
import numpy as np
from cryptography.fernet import Fernet

class BaseEngine(object):
    def __init__(self, engine_path, imgsz=(640,640), encryp_password='s-hYSuK2Uu24huh8264CRagzv5WtGFlbx46i0k8tJzs='):
        self.imgsz = imgsz
        self.mean = None
        self.std = None
        logger = trt.Logger(trt.Logger.WARNING)
        trt.init_libnvinfer_plugins(logger,'')
        runtime = trt.Runtime(logger)
        fw = Fernet(encryp_password)
        with open(engine_path, "rb") as f:
            serialized_engine = fw.decrypt(f.read())
            
        engine = runtime.deserialize_cuda_engine(serialized_engine)
        self.context = engine.create_execution_context()
        self.inputs, self.outputs, self.bindings = [], [], []
        self.stream = cuda.Stream()
        for binding in engine:
            size = trt.volume(engine.get_binding_shape(binding))
            dtype = trt.nptype(engine.get_binding_dtype(binding))
            host_mem = cuda.pagelocked_empty(size, dtype)
            device_mem = cuda.mem_alloc(host_mem.nbytes)
            self.bindings.append(int(device_mem))
            if engine.binding_is_input(binding):
                self.inputs.append({'host': host_mem, 'device': device_mem})
            else:
                self.outputs.append({'host': host_mem, 'device': device_mem})
                
    def forward(self, img):
        self.inputs[0]['host'] = np.ravel(img)
        # transfer data to the gpu
        for inp in self.inputs:
            cuda.memcpy_htod_async(inp['device'], inp['host'], self.stream)
        # run inference
        self.context.execute_async_v2(
            bindings=self.bindings,
            stream_handle=self.stream.handle)
        # fetch outputs from gpu
        for out in self.outputs:
            cuda.memcpy_dtoh_async(out['host'], out['device'], self.stream)
        # synchronize stream
        self.stream.synchronize()

        return [out['host'] for out in self.outputs]

    def inference(self, image_rgb):
        img = np.ascontiguousarray(image_rgb.transpose(2,0,1)/255.0, dtype=np.float32)
        num, final_boxes, final_scores, final_cls_inds = self.forward(img)
        final_boxes = np.reshape(final_boxes, (-1, 4)).astype(np.int32)
        num = num[0]
        return num, final_boxes, final_scores, final_cls_inds

def precise_sleep(sleep_time):
    start_time = time.time()
    while True:
        if time.time()-start_time>=sleep_time:
            break
    