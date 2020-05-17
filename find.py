import pika
from config import config
import argparse
import logging
import cv2
import os
from PIL import ImageGrab, Image
import time
import numpy as np
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='log/find_error.log')
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=str, default=None, help="The offline video's path")
    parser.add_argument("--log", type=str, default='offline_log/', help="The offline video's log path")
    parser.add_argument("--interval", type=float, default=1.5, help="The interval time to get the frame")
    opt = parser.parse_args()
    try:
        mq_conn = pika.BlockingConnection(pika.ConnectionParameters(config.queue_domain,
                                                                    credentials=pika.PlainCredentials(config.queue_user,
                                                                                                      config.queue_pwd)))
        chan = mq_conn.channel()
        queue = chan.queue_declare(queue=config.queue_name, durable=True)
    except Exception as e:
        logger.error(str(e) + ' can not set a channel')
    else:
        if opt.video:
            os.makedirs(opt.log, exist_ok=True)
            vc = cv2.VideoCapture(opt.video)  # 读入视频文件
            c = 1
            if vc.isOpened():  # 判断是否正常打开
                rval, frame = vc.read()
            else:
                rval = False
            timeF = 100
            while rval:
                rval, frame = vc.read()
                if c % timeF == 0:
                    file_path = config.root_path + config.temp_file + opt.video[:-4] + '_' + str(c) + '.jpg'
                    cv2.imwrite(file_path, frame)
                    try:
                        chan.basic_publish(exchange='', routing_key=config.queue_name,
                                           body=opt.video[:-4] + '_' + str(c) + '.jpg')
                    except Exception as e:
                        logger.error(str(e))

                c = c + 1
                cv2.waitKey(1)
            vc.release()
            chan.close()
        else:
            file_path =  config.root_path + config.temp_file
            time.sleep(3)
            while True:
                img = ImageGrab.grab()
                img = np.array(img.getdata(), np.uint8).reshape(img.size[1], img.size[0], 3)
                img = Image.fromarray(img)
                time_stamp = str(int(time.time()))
                img.save(file_path + time_stamp + '.jpg')
                try:
                    chan.basic_publish(exchange='', routing_key=config.queue_name,
                                       body=time_stamp + '.jpg')
                except Exception as e:
                    logger.error(str(e))
                time.sleep(opt.interval)

        #
