import mouse_driver.ghub_mouse as ghub

def mouse_move(rel_x,rel_y):
    ghub.mouse_xy(round(rel_x), round(rel_y))