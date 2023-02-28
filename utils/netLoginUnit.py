# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# File       : netLoginUnit.py
# Time       ：2022/2/6 21:43
# Author     ：Lex
# Email      : 2983997560@qq.com   
# Description：瑞科网络验证 www.ruikeyz.com
# 视频教程：https://www.bilibili.com/video/BV1v44y1T7ki/
"""
import time
import json
import requests
import uuid
import numpy as np
from rich import print

def verify_identity(card_num):
    try:
        login = NetLogin(card_num)
        login.loginInit()
        login_status = login.loginCheck()
    
        # If login fails, print the error message and wait indefinitely
        if login_status[0] == 0:
            print(login_status[1])
            time.sleep(np.Inf)
        else:
            print(f"登陆成功, 到期时间: {login_status[1]}")
    except Exception as e:
        print(f"登陆失败 {e}")
        time.sleep(np.Inf)

class NetLogin:
    """ 瑞科网络验证 """
    def __init__(self, cardnum):
        self.cardnum = cardnum
        self.url = "http://api.ruikeyz.com/netver/webapi"
        self.heartbeatkey = ""
        self.token = ""
        self.endtime = ""
        # self.maccode = "获取本机Mac地址"   # Mac 地址需获取
        self.maccode = hex(uuid.getnode())
        self.versionname = "v1.0"
        self.status = None

        self.param = {
            "businessid": None,
            "encrypttypeid": 0,
            "platformusercode": "3c4759f4c3437892", #平台用户编码：后台->个人中心->个人详情->平台用户编码，进行获取
            "goodscode": "3b63dd86f1708d1d",        #软件编码:软件管理->软件列表->软件编码，进行获取
            "inisoftkey": "",
            "timestamp": None,
            "data": None,
            "sign": "",
            "platformtypeid": 1,   #此处写死成1
        }
        

    def loginInit(self):
        """ 卡密初始化 """
        timestamp = int(round(time.time() * 1000))
        send_data = {
            "maccode": self.maccode,
            "versionname": self.versionname,
            "timestamp": timestamp,
            "requestflag": str(timestamp)
        }

        data_json = json.dumps(send_data)
        param = self.param
        param["businessid"] = 1
        param["timestamp"] = int(round(time.time() * 1000))
        param["data"] = data_json

        response = requests.post(self.url, data=param)
        # print(response.text)
        re_data = requests.post(self.url, json=param, verify=False).json()
        if re_data["code"] == 0:
            # 成功
            # 请求标识 验证
            json_data = eval(re_data["data"])
            if json_data["requestflag"] == str(timestamp):
                # 初始化成功
                self.param["inisoftkey"] = json_data["inisoftkey"]
                return 1, "初始化成功"
        else:
            return 0, "初始化失败, %s" % re_data["msg"]
        return

    def loginCheck(self):
        """ 卡密登陆 """
        timestamp = int(round(time.time() * 1000))
        send_data = {
            "cardnum": self.cardnum,
            "maccode": self.maccode,
            "timestamp": timestamp,
            "requestflag": str(timestamp)
        }

        data_json = json.dumps(send_data)
        param = self.param
        param["businessid"] = 4
        param["timestamp"] = int(round(time.time() * 1000))
        param["data"] = data_json

        re_data = requests.post(self.url, json=param, verify=False).json()
        if re_data["code"] == 0:
            # 成功
            # 请求标识 验证
            json_data = eval(re_data["data"])

            if json_data["requestflag"] == str(timestamp):
                # 初始化成功
                self.heartbeatkey = json_data["heartbeatkey"]
                self.token = json_data["token"]
                self.endtime = json_data["endtime"]
                self.status = 1
                return 1, json_data["endtime"]
        else:
            return 0, "登陆失败, %s" % re_data["msg"]

    def loginHeart(self):
        """ 心跳 """
        timestamp = int(round(time.time() * 1000))
        send_data = {
            "cardnumorusername": self.cardnum,
            "maccode": self.maccode,
            "token": self.token,
            "heartbeatkey": self.heartbeatkey,
            "timestamp": timestamp,
            "requestflag": str(timestamp)
        }

        data_json = json.dumps(send_data)
        param = self.param
        param["businessid"] = 5
        param["timestamp"] = int(round(time.time() * 1000))
        param["data"] = data_json

        re_data = requests.post(self.url, json=param, verify=False).json()
        if re_data["code"] == 0:
            # 成功
            # 请求标识 验证
            json_data = eval(re_data["data"])

            if json_data["requestflag"] == str(timestamp):
                # 初始化成功
                self.heartbeatkey = json_data["heartbeatkey"]
                self.endtime = json_data["endtime"]
                self.status = 1
                return 1, "心跳验证成功"
        else:
            return 0, "心跳验证失败, %s" % re_data["msg"]

    def loginExit(self):
        """ 退出登陆"""
        timestamp = int(round(time.time() * 1000))
        send_data = {
            "cardnumorusername": self.cardnum,
            "maccode": self.maccode,
            "token": self.token,
            "timestamp": timestamp
        }

        data_json = json.dumps(send_data)
        param = self.param
        param["businessid"] = 7
        param["timestamp"] = int(round(time.time() * 1000))
        param["data"] = data_json

        re_data = requests.post(self.url, json=param, verify=False).json()
        if re_data["code"] == 0:
            # 成功
            # 请求标识 验证
            self.status = 0
            return 1, "退出成功"
        else:
            return 0, "退出失败, %s" % re_data["msg"]

    def loginUnbind(self):
        """ 解绑 """
        timestamp = int(round(time.time() * 1000))
        send_data = {
            "cardnumorusername": self.cardnum,
            "maccode": self.maccode,
            "timestamp": timestamp,
            "requestflag": str(timestamp)
        }

        data_json = json.dumps(send_data)
        param = self.param
        param["businessid"] = 9
        param["timestamp"] = int(round(time.time() * 1000))
        param["data"] = data_json

        re_data = requests.post(self.url, json=param, verify=False).json()
        if re_data["code"] == 0:
            self.status = 0
            return 1, "解绑成功"
        else:
            return 0, "解绑失败"

if __name__ == "__main__":
    # 初始化
    login = NetLogin("test-bf68347d0ad75a4c")
    re_init = login.loginInit()
    # if re_init[0] == 0:
    #     print(re_init[1])
    #     exit()

    # 登陆
    re_login = login.loginCheck()
    if re_login[0] == 0:
        print(re_login[1])
        exit()
    else:
        print("登陆成功, 到期时间: %s" % re_login[1])

    # 心跳
    re_heart = login.loginHeart()
    if re_heart[0] == 0:
        print(re_heart[1])
        exit()
    else:
        print(re_heart[1])

    # 退出
    re_exit = login.loginExit()
    if re_exit[0] == 0:
        print(re_exit[1])
        exit()
    else:
        print(re_exit[1])

    # 解绑
    re_unbind = login.loginUnbind()
    if re_unbind[0] == 0:
        print(re_unbind[1])
        exit()
    else:
        print(re_unbind[1])

    print("测试完成")