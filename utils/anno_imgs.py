import os
from .InferenceEngine import screen_shot_init,get_screen_shot, BaseEngine
from tensorrt_python.export_to_trt import export_to_trt
import argparse
import cv2
from tqdm import tqdm

EXTENSION = ['.jpg', '.png', '.jpeg']

def xyxy2xywh(box):
    x1, y1, x2, y2 = box
    return [(x1+x2)/2, (y1+y2)/2, x2 - x1, y2 - y1]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='YOLOV7')
    parser.add_argument('--onnx_path', type=str, default='weights/best.onnx', help='onnx path')
    parser.add_argument('--engine_path', type=str, default='weights/best.trt', help='model path')
    parser.add_argument('--data_dir', type=str, default='data', help='data dir')
    args = parser.parse_args()

    if not os.path.exists(args.engine_path):
        print('---------------------Building engine, please wait for a while (about 10 mins)---------------------')
        export_to_trt(onnx=args.onnx_path, engine=args.engine_path)

    image_dir = os.path.join(args.data_dir, 'images')
    assert os.path.exists(image_dir)
    label_dir = os.path.join(args.data_dir, 'labels')
    if not os.path.exists(label_dir):
        os.mkdir(label_dir)
    engine = BaseEngine(args.engine_path)
    # all the images in the image_dir will be processed, then save to label_dir with yolov7 format
    for image_name in tqdm(os.listdir(image_dir)):
        if not os.path.splitext(image_name)[-1].lower() in EXTENSION:
            continue
        image_path = os.path.join(image_dir, image_name)
        image = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (640, 640))
        num, final_boxes, final_scores, final_cls_inds = engine.inference(image)
        final_boxes = final_boxes/640
        txt_list = []
        for i in range(num):
            box = xyxy2xywh(final_boxes[i])
            txt_list.append([final_cls_inds[i], *box])
        with open(os.path.join(label_dir, image_name[:image_name.rfind('.')]+'.txt'), 'w') as f:
            for txt in txt_list:
                f.write(' '.join([str(x) for x in txt]))
                f.write('\n')
        
    