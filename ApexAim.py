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
from tensorrt_python.export import export_trt
from netLoginUnit import NetLogin
import yaml

class ApexAim:
    def __init__(self, config_path='configs/default.yaml', onnx_path='weights/best.onnx', engine_path='weights/best.trt', detect_length=640):
        config = yaml.load(open(config_path, 'r'), Loader=yaml.FullLoader)
        self.args = argparse.Namespace(**config)
        self.verify_card_num()
        self.detect_length = detect_length
        self.shooting = False

        # default settings by game
        self.axis_move_factor = 1280/self.args.resolution_x 
        scale = self.args.resolution_x/1920 # test on 1920*1080
        for key in self.args.__dict__:
            if 'dis' in key:
                self.args.__dict__[key] *= scale
        
        # model settings
        self.build_trt_model(onnx_path, engine_path)
        self.engine = BaseEngine(engine_path)
        self.init_camera()
        
        # mouse settings
        self.pidx = PID(self.args.pidx_kp, self.args.pidx_kd, self.args.pidx_ki, setpoint=0, sample_time=0.001,)
        self.pidy = PID(self.args.pidy_kp, self.args.pidy_kd, self.args.pidy_ki, setpoint=0, sample_time=0.001,)
        self.pidx(0),self.pidy(0)
        self.mouse_abs_x, self.mouse_abs_y = self.screen_width//2, self.screen_height//2
        self.mouse_x, self.mouse_y = self.mouse_abs_x - self.base_width , self.mouse_abs_y - self.base_height
        self.lock_mode=False
        self.listener = Listener(on_click=self.on_click)
        self.listener.start()

        # speed test
        if self.args.speed_test:
            self.speed_test()

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
            export_trt(onnx=onnx_path, engine=engine_path)

    def init_camera(self):
        self.screen_width, self.screen_height = pyautogui.size()
        self.base_height, self.base_width=self.screen_height//2-self.detect_length//2,self.screen_width//2-self.detect_length//2
        if self.args.mss:
            self.camera = mss()
            self.region = {"top": self.base_height, "left": self.base_width, "width": self.detect_length, "height": self.detect_length}
        else:
            self.camera = dxcam.create(region = (self.base_width,self.base_height,self.screen_width//2+self.detect_length//2,self.screen_height//2+self.detect_length//2))#left,top,right,bottom

    def get_screen_shot(self):
        if self.args.mss:
            return cv2.cvtColor(np.ascontiguousarray(np.array(self.camera.grab(self.region))), cv2.COLOR_BGR2RGB)
        # dxcam
        while True:
            img = self.camera.grab()
            if img is not None:
                return img

    def on_click(self, x, y, button, pressed):
        if button == getattr(Button,self.args.mouse_button):
            if pressed:
                self.lock_mode = True
                print('开启锁定...')
            else:
                self.lock_mode = False
                print('关闭锁定')
        if self.args.print_button:
            print(f'按键 {button.name} 被摁下')
    
    def speed_test(self):
        t = time.perf_counter()
        for _ in range(100):
            img = self.get_screen_shot()
        print(f'截图100次平均耗时: {(time.perf_counter()-t)/100:.3f}s 帧率: {100/(time.perf_counter()-t):.3f}FPS')
        t = time.perf_counter()
        for _ in range(100):
            self.engine.inference(img)
        print(f'推理100次平均耗时: {(time.perf_counter()-t)/100:.3f}s 帧率: {100/(time.perf_counter()-t):.3f}FPS')
        t = time.perf_counter()
        for _ in range(100):
            self.forward()
        print(f'总体100次平均耗时: {(time.perf_counter()-t)/100:.3f}s 帧率: {100/(time.perf_counter()-t):.3f}FPS')

    def calculate_target_info(self):
        self.target_info_list = []
        for xyxy, conf, cls in zip(self.xyxy_list, self.conf_list, self.cls_list):
            cls_name = self.args.label_list[cls]
            x1, y1, x2, y2 = xyxy.tolist()
            target_x , target_y = (x1+x2)/2, (y1+y2)/2-self.args.pos_factor*(y2-y1)
            move_dis = ((target_x-self.mouse_x)**2+(target_y-self.mouse_y)**2)**(1/2)
            if cls_name in self.args.target_label_list and conf >= self.args.conf and move_dis < self.args.max_lock_dis:
                self.target_info_list.append([target_x, target_y, move_dis, cls_name])
        # sort target_info_list on cls_list order, then min dis
        self.target_info_list = sorted(self.target_info_list, key=lambda x: (self.args.target_label_list.index(x[3]), x[2]))

    def calculate_move_dis(self):
        target_x, taret_y, move_dis = self.target_info_list[0][:3]
        move_rel_x, move_rel_y = (target_x-self.mouse_x)*self.axis_move_factor, (taret_y-self.mouse_y)*self.axis_move_factor
        if self.args.use_pid and move_dis < self.args.use_pid_max_dis:
            move_rel_x = self.pidx(self.args.smooth* atan(float(-move_rel_x) / self.detect_length) * self.detect_length)
            move_rel_y = self.pidy(self.args.smooth* atan(float(-move_rel_y) / self.detect_length) * self.detect_length)
        if move_dis > self.args.max_step_dis:
            move_rel_x = move_rel_x/move_dis*self.args.max_step_dis
            move_rel_y = move_rel_y/move_dis*self.args.max_step_dis
        return move_rel_x, move_rel_y, move_dis

    def move_shoot(self):
        if len(self.target_info_list) > 0 and self.lock_mode:
            move_rel_x, move_rel_y, move_dis = self.calculate_move_dis()
            mouse_move(move_rel_x, move_rel_y)
            if not self.shooting and self.args.auto_shoot and move_dis < self.args.max_shoot_dis:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                self.shooting=True
        if self.shooting and (len(self.target_info_list) == 0 or not self.lock_mode) and self.args.auto_shoot:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            self.shooting=False
        self.pidx(0), self.pidy(0)

    def visualization(self):
        for xyxy, conf, cls in zip(self.xyxy_list, self.conf_list, self.cls_list):
            cls_name = self.args.label_list[cls]
            x1, y1, x2, y2 = xyxy.tolist()
            label = f'{cls_name} {conf:.2f}'
            color = (0, 255, 0) if conf > self.args.conf else (0, 0, 255)
            cv2.putText(self.img, label, (x1, y1 - 25), 0, 0.7, color, 2)
            cv2.rectangle(self.img, (x1, y1), (x2, y2), color, 2)
        if len(self.target_info_list) > 0:
            target_x, taret_y, move_dis = self.target_info_list[0][:3]
            cv2.circle(self.img, (int(target_x), int(taret_y)), 5, (255, 0, 0), -1)
            cv2.line(self.img, (int(self.mouse_x), int(self.mouse_y)), (int(target_x), int(taret_y)), (255, 0, 0), 2)
            cv2.putText(self.img, f'{move_dis:.2f}', (int(target_x), int(taret_y)), 0, 0.7, (255, 0, 0), 2)
        cv2.imshow('Detection Window', cv2.cvtColor(self.img,cv2.COLOR_RGB2BGR))
        if cv2.waitKey(25) & 0xFF == ord('q'):
            cv2.destroyAllWindows()

    def forward(self):
        self.img = self.get_screen_shot()
        _, self.xyxy_list, self.conf_list, self.cls_list = self.engine.inference(self.img)
        self.calculate_target_info()
        self.move_shoot()
        
        if self.args.visualization:
            self.visualization()
            
        precise_sleep(self.args.delay)

if __name__ == '__main__':
    apex = ApexAim()
    heart_time = time.perf_counter()
    while True:
        apex.forward()
        if time.perf_counter() - heart_time > 600:
            apex.login.loginHeart()
            heart_time = time.perf_counter()