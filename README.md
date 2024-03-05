

def save_screenshot(queue, dir='screenshot', freq=0.5):
        if not os.path.exists(dir):
            os.makedirs(dir)
        start_time = time.time()
        while True:
            img, locking, nums = queue.get()
            if (locking or nums > 10000) and (time.time() - start_time >= freq): # having bounding boxes or locking will get screenshot
                img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                cv2.imwrite(os.path.join(dir, f'{time.time():.5f}.png'), img_bgr)
                start_time = time.time()
