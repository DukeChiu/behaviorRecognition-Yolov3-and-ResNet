import torch
from torch import nn
from PIL import Image
from torchvision import transforms
import numpy as np
import torch.nn.functional as F
from torchvision.models import resnet152


class ResNet152(nn.Module):
    def __init__(self):
        super(ResNet152, self).__init__()
        net = resnet152(pretrained=True)
        user_defined_resnet152 = nn.Sequential()
        for name, module in net.named_children():
            # print(name, module)
            if name != 'fc' and name:
                user_defined_resnet152.add_module(name, module)
        user_defined_resnet152.add_module('flatten', FlattenLayer())
        user_defined_resnet152.add_module('fc', nn.Linear(2048, 4))
        self.mode = 'test'
        self.net = user_defined_resnet152
        self.loss = None
        self.acc = None

    def forward(self, x, target=None):
        # print(self.device)
        # return x
        y_hat = self.net(x)
        if self.mode == 'train':
            assert target is not None, 'target mustn\'t  be None'
            # print(y_hat)
            self.loss = nn.CrossEntropyLoss()(y_hat, target)
            self.acc = (y_hat.argmax(dim=1) == target).sum().float().item()
        return y_hat.argmax(dim=1)

    def eval_acc(self, data_iter, the_device=None):
        net = self.net
        acc_sum, n = 0.0, 0
        with torch.no_grad():
            for x, y in data_iter:
                net.eval()
                acc_sum += (net(x.to(the_device)).argmax(dim=1) == y.to(the_device)).float().sum().cpu().item()
                net.train()
                n += y.shape[0]
        return acc_sum / n, n


class FlattenLayer(nn.Module):
    def __init__(self):
        super(FlattenLayer, self).__init__()

    def forward(self, x):
        return x.view(x.shape[0], -1)


def pad_to_square(img, pad_value):
    c, h, w = img.shape
    dim_diff = np.abs(h - w)
    pad1, pad2 = dim_diff // 2, dim_diff - dim_diff // 2
    pad = (0, 0, pad1, pad2) if h <= w else (pad1, pad2, 0, 0)
    img = F.pad(img, pad, "constant", value=pad_value)
    return img, pad


def resize(image, size=128):
    image = F.interpolate(image.unsqueeze(0), size=size, mode="nearest").squeeze(0)
    return image


if __name__ == '__main__':
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = ResNet152()
    model.to(device)
    trans = transforms.ToTensor()
    img = Image.open('000002_worker_0.jpg')
    img.convert('RGB')
    value = trans(img)
    value, pad = pad_to_square(value, 0)
    value = resize(value, 128)
    value = torch.unsqueeze(value, dim=0).float()
    # this is a
    res = model(value.to(device))
    print(res)
