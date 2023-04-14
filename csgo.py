from AimBot import AimBot
import multiprocessing
import time
from mouse_driver.MouseMove import mouse_move
from pynput.mouse import Button, Listener, Controller


class CSGOAimBot(AimBot):
    def __init__(self, config_path, onnx_path, engine_path):
        super().__init__(config_path, onnx_path, engine_path)
        self.controller =  Controller()

    def initialize_params(self):
        super().initialize_params()
        self.smooth = self.args.smooth * 2700 / self.args.resolution_x # default settings by game
    
    def lock_target(self, target_sort_list):
        if len(target_sort_list) > 0 and self.locking:
            move_rel_x, move_rel_y, move_dis = self.get_move_dis(target_sort_list)
            mouse_move(move_rel_x, move_rel_y) # //2 for solving the shaking problem when
            print(move_dis)
            if move_dis < self.args.max_shoot_dis:
               self.controller.click(Button.left, 1)
        self.pidx(0), self.pidy(0)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    csgo = CSGOAimBot(config_path='configs/csgo.yaml', onnx_path='weights/best_csgo.onnx', engine_path='weights/best_csgo.trt')
    while True:
        data = csgo.forward()