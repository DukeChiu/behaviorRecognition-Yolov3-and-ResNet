from .models import ResNet152
import torch


class Classification:
    def __init__(self, pth_path='config/resnet152_ckpt_20.pth'):
        path_root = '\\'.join(str(__file__).split('\\')[:-1]) + '\\'
        self.__model = ResNet152()
        pth_load = torch.load(path_root + pth_path)
        if torch.cuda.is_available():
            self.__device = torch.device('cuda')
        else:
            self.__device = torch.device('cpu')
            pth_load = torch.load(pth_path, map_location='cpu')
        self.__model.to(self.__device)
        self.__model.load_state_dict(pth_load)
        self.__model.eval()
        self.__model.mode = 'test'

    def classify(self, matrix):
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        with torch.no_grad():
            res = self.__model(matrix.to(device))
        return res


classify_handler = Classification()
