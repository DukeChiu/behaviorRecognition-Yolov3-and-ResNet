import numpy as np
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
from detection import detect_handler
import torch
from classification import classify_handler

# import os
# import cv2


class Judge:
    def __init__(self):
        self.detect_handler = detect_handler
        self.classify_handler = classify_handler

    def judge(self, file):
        # print(file)
        img_origin = Image.open(file)
        img_value = transforms.ToTensor()(img_origin.convert('RGB')).float()
        img_value = self.__pad_to_square(img_value, 0)
        img_value = self.__resize(img_value, 416)
        img_value = torch.unsqueeze(img_value, dim=0)
        person_boxes = self.detect_handler.detect(img_value, img_origin.size[::-1])
        if len(person_boxes) == 0:
            return False
        classify_res = self.classify_handler.classify(self.__format_boxes(img_origin, person_boxes))
        # print(classify_res)
        res = classify_res[torch.where(classify_res > 1)]
        return res.shape[0] != 0

    def __pad_to_square(self, img, pad_value):
        c, h, w = img.shape
        dim_diff = np.abs(h - w)
        pad1, pad2 = dim_diff // 2, dim_diff - dim_diff // 2
        pad = (0, 0, pad1, pad2) if h <= w else (pad1, pad2, 0, 0)
        img = F.pad(img, pad, "constant", value=pad_value)

        return img

    def __resize(self, img, size=128):
        img = F.interpolate(img.unsqueeze(0), size=size, mode="nearest").squeeze(0)
        return img

    def __format_boxes(self, img_orign, person_boxes):
        person_value = []
        for person_box in person_boxes:
            person_crop = img_orign.crop((person_box[i] for i in range(4)))
            # person_crop.save('test_2.jpg')
            person_crop.convert('RGB')
            person_crop_value = self.__resize(self.__pad_to_square(transforms.ToTensor()(person_crop).float(), 0))
            person_value.append(person_crop_value)
        return torch.stack(person_value, dim=0)


if __name__ == '__main__':
    judge_handler = Judge()
    print(judge_handler.judge('000812.jpg'))
