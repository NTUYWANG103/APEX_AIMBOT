from ApexAim import ApexAim
import time
import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()
    apex = ApexAim(config_path='configs/default.yaml')
    heart_time = time.time()
    while True:
        apex.forward()
        if time.time() - heart_time > 600:
            # apex.login.loginHeart()
            heart_time = time.time()
