from .models import *
import torch
from torchvision import transforms
from PIL import Image
import os


def _rescale_boxes(boxes, current_dim, original_shape):
    # print(original_shape)
    orig_h, orig_w = original_shape
    # print(orig_h, orig_w)
    pad_x = max(orig_h - orig_w, 0) * (current_dim / max(original_shape))
    pad_y = max(orig_w - orig_h, 0) * (current_dim / max(original_shape))
    unpad_h = current_dim - pad_y
    unpad_w = current_dim - pad_x
    boxes[:, 0] = ((boxes[:, 0] - pad_x // 2) / unpad_w) * orig_w
    boxes[:, 1] = ((boxes[:, 1] - pad_y // 2) / unpad_h) * orig_h
    boxes[:, 2] = ((boxes[:, 2] - pad_x // 2) / unpad_w) * orig_w
    boxes[:, 3] = ((boxes[:, 3] - pad_y // 2) / unpad_h) * orig_h
    return boxes


class Detect:
    def __init__(self, *args):
        path_root = '\\'.join(str(__file__).split('\\')[:-1]) + '\\'
        cfg_path, pth_path, classes_path = tuple(map(lambda x: path_root + x, args))
        # print(os.path.abspath(__file__))
        self.__model = Darknet(cfg_path, 416)
        with open(classes_path, 'r') as f:
            self.__classes = f.read().split('\n')[:-1]
        pth_load = torch.load(pth_path)
        if torch.cuda.is_available():
            self.__device = torch.device('cuda')
        else:
            self.__device = torch.device('cpu')
            pth_load = torch.load(pth_path, map_location='cpu')
        self.__model.to(self.__device)
        self.__model.load_state_dict(pth_load)
        self.__model.eval()

    def detect(self, img, img_shape) -> list:
        Tensor = torch.cuda.FloatTensor if torch.cuda.is_available() else torch.FloatTensor
        input_img = Variable(img.type(Tensor))
        with torch.no_grad():
            detections = self.__model(input_img)
            detections = non_max_suppression(detections, 0.9, 0.2)
        res_detect = []
        if detections[0] is not None:
            detections = detections[0]
            detections = _rescale_boxes(detections, 416, img_shape[:2])
            for detection in detections:
                detection_ = list(map(float, detection))
                # print(detection_)
                if self.__classes[int(detection_[-1])] == 'person':
                    res_detect.append(detection_[:4] + detection_[-2:-1])
            if len(res_detect) > 0:
                res_detect = self.__format_one_detect(res_detect, img_shape[:2])
        return res_detect

    @staticmethod
    def __format_one_detect(this_detect: list, im_size) -> list:
        height, width = im_size
        this_detect = np.array(this_detect)
        this_detect[:, 0] = np.maximum(np.minimum(this_detect[:, 0], width - 1), 0)
        this_detect[:, 1] = np.maximum(np.minimum(this_detect[:, 1], height - 1), 0)
        this_detect[:, 2] = np.maximum(np.minimum(this_detect[:, 2], width - 1), 0)
        this_detect[:, 3] = np.maximum(np.minimum(this_detect[:, 3], height - 1), 0)
        return this_detect.tolist()


detect_handler = Detect('config/yolov3.cfg', 'config/yolov3_ckpt_170.pth', 'config/classes.names')
