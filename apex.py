from AimBot import AimBot
import multiprocessing
import time


class ApexAimBot(AimBot):
    def __init__(self, config_path, onnx_path, engine_path):
        super().__init__(config_path, onnx_path, engine_path)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    apex = ApexAimBot(config_path='configs/apex.yaml', onnx_path='weights/best_apex.onnx', engine_path='weights/best_apex.trt')
    heart_time = time.time()
    while True:
        apex.forward()
        if time.time() - heart_time > 600:
            apex.login.loginHeart()
            heart_time = time.time()