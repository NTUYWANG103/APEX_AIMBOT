import mouse_driver.ghub_mouse as ghub

def mouse_move(rel_x,rel_y):
    ghub.mouse_xy(round(rel_x), round(rel_y))


if __name__ == "__main__":
    import time
    trials = 10000
    start_time = time.time()
    for i in range(trials):
        mouse_move(100,0)
        mouse_move(-100,0)
    fps = trials/(time.time()-start_time)
    print(fps)