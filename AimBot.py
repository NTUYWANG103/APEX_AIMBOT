import os
import time
import numpy as np
import pyautogui
import argparse
from pynput.mouse import Button, Listener
import cv2
from mss.windows import MSS as mss
from rich import print
from simple_pid import PID
from math import atan2
from mouse_driver.MouseMove import mouse_move
from utils.InferenceEngine import BaseEngine, precise_sleep
from tensorrt_python.export_to_trt import export_to_trt
from utils.netLoginUnit import verify_identity
import yaml
from multiprocessing import Process, Queue

class AimBot:
    def __init__(self, config_path='configs/default.yaml', onnx_path='weights/best.onnx', engine_path='weights/best.trt'):
        config = yaml.load(open(config_path, 'r'), Loader=yaml.FullLoader)
        self.args = argparse.Namespace(**config)
        self.login = verify_identity(self.args.card_num) # comment this line to ignore log in 

        self.initialize_params()    
        self.build_trt_model(onnx_path, engine_path)
        
        # visualization and screenshot
        self.q_visual, self.q_save = Queue(), Queue()
        if self.args.visualization:
            Process(target=self.visualization, args=(self.args, self.q_visual,)).start()
        if self.args.save_screenshot:
            Process(target=self.save_screenshot, args=(self.q_save,)).start()

        # model settings
        self.engine = BaseEngine(engine_path)
        self.initialize_camera()

        if self.args.speed_test:
            self.speed_test()

        listener = Listener(on_click=self.on_click)
        listener.start()
        print('---------------------启动完成---------------------')
    
    def initialize_params(self):
        self.auto_lock = True
        self.locking=False

        # default settings by game
        self.detect_length = 640
        self.smooth = self.args.smooth * 1920 / self.args.resolution_x # higher resolution requires less move
        self.scale = self.args.resolution_x / 1920 # set hyperparameters on 1920*1080, making all resolution the same effect
        for key in self.args.__dict__:
            if 'dis' in key:
                self.args.__dict__[key] *= self.scale

        # mouse settings
        self.pidx = PID(self.args.pidx_kp, self.args.pidx_kd, self.args.pidx_ki, setpoint=0, sample_time=0.001,)
        self.pidy = PID(self.args.pidy_kp, self.args.pidy_kd, self.args.pidy_ki, setpoint=0, sample_time=0.001,)
        self.pidx(0),self.pidy(0)
        self.detect_center_x, self.detect_center_y = self.detect_length//2, self.detect_length//2

    def build_trt_model(self, onnx_path, engine_path):
        if not os.path.exists(engine_path):
            print('---------------------模型制作中，第一次等待时间较长(大约 10 mins)---------------------')
            export_to_trt(onnx=onnx_path, engine=engine_path)

    def initialize_camera(self):
        self.screen_width, self.screen_height = pyautogui.size()
        self.top, self.left=self.screen_height//2-self.detect_length//2,self.screen_width//2-self.detect_length//2
        self.camera = mss()
        self.region = {"top": self.top, "left": self.left, "width": self.detect_length, "height": self.detect_length}

    def grab_screen(self):
        return cv2.cvtColor(np.asarray(self.camera.grab(self.region)), cv2.COLOR_BGR2RGB)

    def on_click(self, x, y, button, pressed):
        # Turn on and off auto_lock
        if button == getattr(Button, self.args.auto_lock_button) and pressed:
            if self.auto_lock:
                self.auto_lock = False
                print('---------------------自动瞄准已关闭---------------------')
            else:
                self.auto_lock = True
                print('---------------------自动瞄准已开启---------------------')

        # Press the left button to turn on auto aim
        if button == getattr(Button, self.args.mouse_button) and self.auto_lock:
            if pressed:
                self.locking = True
                print('已开启锁定...')
            else:
                self.locking = False
                print('已关闭锁定')

        # Print button press for debugging purposes
        if self.args.print_button:
            print(f'按键 {button.name} 已按下')
    
    def speed_test(self):
        t = time.time()
        for _ in range(100):
            img = self.grab_screen()
        print(f'截图100次平均耗时: {(time.time()-t)/100:.3f}s 帧率: {100/(time.time()-t):.3f}FPS')
        t = time.time()
        for _ in range(100):
            self.engine.inference(img)
        print(f'推理100次平均耗时: {(time.time()-t)/100:.3f}s 帧率: {100/(time.time()-t):.3f}FPS')
        t = time.time()
        for _ in range(100):
            self.forward()
        print(f'总体100次平均耗时: {(time.time()-t)/100:.3f}s 帧率: {100/(time.time()-t):.3f}FPS')

    def sort_target(self, boxes, confidences, classes):
        target_sort_list = []
        for box, conf, cls in zip(boxes, confidences, classes):
            label = self.args.label_list[cls]
            x1, y1, x2, y2 = box.tolist()
            target_x, target_y = (x1 + x2) / 2, (y1 + y2) / 2 - self.args.pos_factor * (y2 - y1)
            move_dis = ((target_x - self.detect_center_x) ** 2 + (target_y - self.detect_center_y) ** 2) ** (1 / 2)
            if label in self.args.enemy_list and conf >= self.args.conf and move_dis < self.args.max_lock_dis:
                target_info = {'target_x': target_x, 'target_y': target_y, 'move_dis': move_dis, 'label': label, 'conf': conf}
                target_sort_list.append(target_info)
        # Sort the list by label and then by distance
        return sorted(target_sort_list, key=lambda x: (x['label'], x['move_dis']))

    def get_move_dis(self, target_sort_list):
        # Get the target with the lowest distance
        target_info = min(target_sort_list, key=lambda x: (x['label'], x['move_dis']))
        target_x, target_y, move_dis = target_info['target_x'], target_info['target_y'], target_info['move_dis']
        # Compute the relative movement needed to aim at the target
        move_rel_x = (target_x - self.detect_center_x) * self.smooth
        move_rel_y = (target_y - self.detect_center_y) * self.smooth
        if move_dis >= self.args.max_step_dis:
            # Limit the movement to the maximum step distance
            move_rel_x = move_rel_x / move_dis * self.args.max_step_dis
            move_rel_y = move_rel_y / move_dis * self.args.max_step_dis
        elif move_dis <= self.args.max_pid_dis:
            # Use a PID controller to smooth the movement
            move_rel_x = self.pidx(atan2(-move_rel_x, self.detect_length) * self.detect_length)
            move_rel_y = self.pidy(atan2(-move_rel_y, self.detect_length) * self.detect_length)
        return move_rel_x, move_rel_y, move_dis

    def lock_target(self, target_sort_list):
        if len(target_sort_list) > 0 and self.locking:
            move_rel_x, move_rel_y, move_dis = self.get_move_dis(target_sort_list)
            mouse_move(move_rel_x, move_rel_y) # //2 for solving the shaking problem when
        self.pidx(0), self.pidy(0)

    def visualization(self, args, queue):
        while True:
            # Retrieve information from queue
            if queue.qsize() > 0:
                while queue.qsize() >= 1: # get tht latest item
                    img, xyxy_list, conf_list, cls_list, target_sort_list, fps_track = queue.get()
                # Draw FPS on image
                cv2.putText(img, f'FPS: {fps_track:.2f}', (10, 30), 0, 0.7, (0, 255, 0), 2)
                # Draw detected targets
                for xyxy, conf, cls in zip(xyxy_list, conf_list, cls_list):
                    cls_name = args.label_list[cls]
                    x1, y1, x2, y2 = xyxy.tolist()
                    label = f'{cls_name} {conf:.2f}'
                    if conf > args.conf:
                        color = (255, 0, 0) if cls_name in self.args.enemy_list else (0, 255, 0)
                    else:
                        color = (0, 0, 255)
                    cv2.putText(img, label, (x1, y1 - 25), 0, 0.7, color, 2)
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                # Draw locked target
                if len(target_sort_list) > 0:
                    target_info = target_sort_list[0]
                    target_x, target_y, move_dis = target_info['target_x'], target_info['target_y'], target_info['move_dis']
                    cv2.circle(img, (int(target_x), int(target_y)), 5, (255, 0, 0), -1)
                    cv2.line(img, (int(self.detect_center_x), int(self.detect_center_y)), (int(target_x), int(target_y)), (255, 0, 0), 2)
                    cv2.putText(img, f'{move_dis:.2f}', (int(target_x), int(target_y)), 0, 0.7, (255, 0, 0), 2)
                # Display image
                cv2.imshow('Detection Window', cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
                if cv2.waitKey(25) & 0xFF == ord('q'):
                    cv2.destroyAllWindows()

    @staticmethod
    def save_screenshot(queue, dir='screenshot', freq=0.5):
        if not os.path.exists(dir):
            os.makedirs(dir)
        start_time = time.time()
        while True:
            img, locking, nums = queue.get()
            if (locking or nums > 0) and (time.time() - start_time >= freq): # having bounding boxes or locking will get screenshot
                img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                cv2.imwrite(os.path.join(dir, f'{time.time():.5f}.png'), img_bgr)
                start_time = time.time()

    def forward(self):
        start_time = time.time()
        img = self.grab_screen()
        nums, boxes, confidences, classes = self.engine.inference(img)
        target_sort_list = self.sort_target(boxes, confidences, classes)
        self.lock_target(target_sort_list)
        fps_track = 1/(time.time()-start_time)

        if self.args.save_screenshot:
            self.q_save.put([img, self.locking, nums])

        if self.args.visualization:
            self.q_visual.put([img, boxes, confidences, classes, target_sort_list, fps_track])

        precise_sleep(self.args.delay)
        

if __name__ == '__main__':
    apex = AimBot()
    heart_time = time.time()
    while True:
        apex.forward()
        if time.time() - heart_time > 600:
            # apex.login.loginHeart()
            heart_time = time.time()