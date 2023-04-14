from AimBot import AimBot
import multiprocessing
import time


class ApexAimBot(AimBot):
    def __init__(self, config_path, onnx_path, engine_path):
        super().__init__(config_path, onnx_path, engine_path)

    def initialize_params(self):
        super().initialize_params()
        self.smooth = self.args.smooth * 1280 / self.args.resolution_x # default settings by game


if __name__ == '__main__':
    multiprocessing.freeze_support()
    apex = ApexAimBot(config_path='configs/apex.yaml', onnx_path='weights/best_apex.onnx', engine_path='weights/best_apex.trt')
    while True:
        apex.forward()