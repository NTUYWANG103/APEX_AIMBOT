import os
import time
import numpy as np
import pyautogui
import argparse
from pynput.mouse import Button, Listener
import cv2
import win32api, win32con
import dxcam
from mss.windows import MSS as mss
from rich import print
from simple_pid import PID
from math import atan
from mouse_driver.MouseMove import mouse_move
from utils.InferenceEngine import BaseEngine, precise_sleep
from tensorrt_python.export_to_trt import export_to_trt
from netLoginUnit import NetLogin
import yaml
from multiprocessing import Process, Queue

class ApexAim:
    def __init__(self, config_path='configs/default.yaml', onnx_path='weights/best.onnx', engine_path='weights/best.trt', detect_length=640):
        config = yaml.load(open(config_path, 'r'), Loader=yaml.FullLoader)
        self.args = argparse.Namespace(**config)
        # self.verify_card_num()
        self.detect_length = detect_length
        self.auto_lock = True
        self.locking=False

        # default settings by game
        self.axis_move_factor = 1280/self.args.resolution_x 
        scale = self.args.resolution_x/1920 # test on 1920*1080
        for key in self.args.__dict__:
            if 'dis' in key:
                self.args.__dict__[key] *= scale

        # mouse settings
        self.pidx = PID(self.args.pidx_kp, self.args.pidx_kd, self.args.pidx_ki, setpoint=0, sample_time=0.001,)
        self.pidy = PID(self.args.pidy_kp, self.args.pidy_kd, self.args.pidy_ki, setpoint=0, sample_time=0.001,)
        self.pidx(0),self.pidy(0)
        self.mouse_x, self.mouse_y = detect_length//2, detect_length//2
        self.queue = Queue()
        
        if self.args.visualization:
            Process(target=self.visualization, args=(self.args, self.queue,)).start()

        # model settings
        self.build_trt_model(onnx_path, engine_path)
        self.engine = BaseEngine(engine_path)
        self.create_camera()

        if self.args.speed_test:
            self.speed_test()

        self.listener = Listener(on_click=self.on_click)
        self.listener.start()

    def verify_card_num(self):
        self.login = NetLogin(self.args.card_num)
        self.login.loginInit()
        re_login = self.login.loginCheck()
        if re_login[0] == 0:
            print(re_login[1])
            precise_sleep(np.Inf)
        else:
            print(f"登陆成功, 到期时间: {re_login[1]}")

    def build_trt_model(self, onnx_path, engine_path):
        if not os.path.exists(engine_path):
            print('---------------------模型制作中，第一次等待时间较长(大约 10 mins)---------------------')
            export_to_trt(onnx=onnx_path, engine=engine_path)

    def create_camera(self):
        self.screen_width, self.screen_height = pyautogui.size()
        self.base_height, self.base_width=self.screen_height//2-self.detect_length//2,self.screen_width//2-self.detect_length//2
        if self.args.mss:
            self.camera = mss()
            self.region = {"top": self.base_height, "left": self.base_width, "width": self.detect_length, "height": self.detect_length}
        else:
            self.camera = dxcam.create(region = (self.base_width,self.base_height,self.screen_width//2+self.detect_length//2,self.screen_height//2+self.detect_length//2))#left,top,right,bottom

    def grab_screen(self):
        if self.args.mss:
            return cv2.cvtColor(np.ascontiguousarray(np.array(self.camera.grab(self.region))), cv2.COLOR_BGR2RGB)
        # dxcam
        while True:
            img = self.camera.grab()
            if img is not None:
                return img

    def on_click(self, x, y, button, pressed):
        # Turn on and off auto_lock
        if button == getattr(Button, self.args.auto_lock_button) and pressed:
            if self.auto_lock:
                self.auto_lock = False
                print('关闭自动瞄准')
            else:
                self.auto_lock = True
                print('开启自动瞄准')

        # Press the left button to turn on auto aim
        if button == getattr(Button,self.args.mouse_button) and self.auto_lock:
            if pressed:
                self.locking = True
                print('开启锁定...')
            else:
                self.locking = False
                print('关闭锁定')
        if self.args.print_button:
            print(f'按键 {button.name} 被摁下')
    
    def speed_test(self):
        t = time.perf_counter()
        for _ in range(100):
            img = self.grab_screen()
        print(f'截图100次平均耗时: {(time.perf_counter()-t)/100:.3f}s 帧率: {100/(time.perf_counter()-t):.3f}FPS')
        t = time.perf_counter()
        for _ in range(100):
            self.engine.inference(img)
        print(f'推理100次平均耗时: {(time.perf_counter()-t)/100:.3f}s 帧率: {100/(time.perf_counter()-t):.3f}FPS')
        t = time.perf_counter()
        for _ in range(100):
            self.forward()
        print(f'总体100次平均耗时: {(time.perf_counter()-t)/100:.3f}s 帧率: {100/(time.perf_counter()-t):.3f}FPS')

    def get_target_info(self, xyxy_list, conf_list, cls_list):
        target_info_list = []
        for xyxy, conf, cls in zip(xyxy_list, conf_list, cls_list):
            cls_name = self.args.label_list[cls]
            x1, y1, x2, y2 = xyxy.tolist()
            target_x, target_y = (x1+x2)/2, (y1+y2)/2-self.args.pos_factor*(y2-y1)
            move_dis = ((target_x-self.mouse_x)**2+(target_y-self.mouse_y)**2)**(1/2)
            if cls_name in self.args.label_lock_list and conf >= self.args.conf and move_dis < self.args.max_lock_dis:
                target_info_list.append({'target_x':target_x, 'target_y':target_y, 'move_dis':move_dis, 'cls_name':cls_name, 'conf':conf})
        # sort target_info_list on cls_list order, then min dis
        target_info_list = sorted(target_info_list, key=lambda x: x['move_dis'])
        return target_info_list

    def get_move_info(self, target_info_list):
        target_info = target_info_list[0]
        target_x, target_y, move_dis = target_info['target_x'], target_info['target_y'], target_info['move_dis']
        move_rel_x, move_rel_y = (target_x-self.mouse_x)*self.axis_move_factor, (target_y-self.mouse_y)*self.axis_move_factor
        if move_dis > self.args.max_step_dis:
            move_rel_x = move_rel_x/move_dis*self.args.max_step_dis
            move_rel_y = move_rel_y/move_dis*self.args.max_step_dis
        elif self.args.use_pid and move_dis < self.args.use_pid_max_dis:
            move_rel_x = self.pidx(self.args.smooth* atan(float(-move_rel_x) / self.detect_length) * self.detect_length)
            move_rel_y = self.pidy(self.args.smooth* atan(float(-move_rel_y) / self.detect_length) * self.detect_length)
        return move_rel_x, move_rel_y, move_dis

    def lock(self, target_info_list):
        if len(target_info_list) > 0 and self.locking:
            move_rel_x, move_rel_y, move_dis = self.get_move_info(target_info_list)
            mouse_move(move_rel_x, move_rel_y)
        self.pidx(0), self.pidy(0)

    def visualization(self, args, queue):
        start_time = time.perf_counter()
        while True:
            img, xyxy_list, conf_list, cls_list, target_info_list = queue.get()
            # record fps
            fps = 1/(time.perf_counter()-start_time)
            start_time = time.perf_counter()
            cv2.putText(img, f'FPS: {fps:.2f}', (10, 30), 0, 0.7, (0, 255, 0), 2)
            # draw detected targets
            for xyxy, conf, cls in zip(xyxy_list, conf_list, cls_list):
                cls_name = args.label_list[cls]
                x1, y1, x2, y2 = xyxy.tolist()
                label = f'{cls_name} {conf:.2f}'
                color = (0, 255, 0) if conf > args.conf else (0, 0, 255)
                cv2.putText(img, label, (x1, y1 - 25), 0, 0.7, color, 2)
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            # draw locked target
            if len(target_info_list) > 0:
                target_info = target_info_list[0]
                target_x, target_y, move_dis = target_info['target_x'], target_info['target_y'], target_info['move_dis']
                cv2.circle(img, (int(target_x), int(target_y)), 5, (255, 0, 0), -1)
                cv2.line(img, (int(self.mouse_x), int(self.mouse_y)), (int(target_x), int(target_y)), (255, 0, 0), 2)
                cv2.putText(img, f'{move_dis:.2f}', (int(target_x), int(target_y)), 0, 0.7, (255, 0, 0), 2)
            cv2.imshow('Detection Window', cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()

    def forward(self):
        img = self.grab_screen()
        _, xyxy_list, conf_list, cls_list = self.engine.inference(img)
        target_info_list = self.get_target_info(xyxy_list, conf_list, cls_list)
        self.lock(target_info_list)

        if self.args.visualization:
            self.queue.put([img, xyxy_list, conf_list, cls_list, target_info_list])

        precise_sleep(self.args.delay)

if __name__ == '__main__':
    apex = ApexAim()
    heart_time = time.perf_counter()
    while True:
        apex.forward()
        if time.perf_counter() - heart_time > 600:
            apex.login.loginHeart()
            heart_time = time.perf_counter()