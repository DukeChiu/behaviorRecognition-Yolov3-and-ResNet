import threading
import os
import cv2
import pika
import shutil
from config import config
from judge import Judge
import logging
import math
import inspect
import ctypes
import time
from tkinter import messagebox

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='log/error.log')
logger = logging.getLogger(__name__)
judge_handler = Judge()


def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


def customer_thread():
    try:
        mq_conn = pika.BlockingConnection(
            pika.ConnectionParameters(config.queue_domain,
                                      credentials=pika.PlainCredentials(config.queue_user, config.queue_pwd)))
        chan = mq_conn.channel()
        chan.queue_declare(queue=config.queue_name, durable=True)
    except Exception as e:
        print('An Error occurs, check it at error.log')
        logger.error(str(e) + ' can not set a server channel')
    else:
        try:
            chan.basic_qos(prefetch_count=1)
            # print(config.queue_name)
            chan.basic_consume(queue='monitor', on_message_callback=callback)
            chan.start_consuming()
        except Exception as e:
            print('An Error occurs, check it at error.log')
            logger.error(str(e) + 'can not get a data from the queue')


def callback(channel, method, properties, body):
    try:
        process(str(body, encoding='utf-8'))
    except Exception as e:
        print('An Error occurs, check it at error.log')
        logger.error(str(e) + ' when judge photo')
    channel.basic_ack(delivery_tag=method.delivery_tag, multiple=True)


def process(file):
    # logger.error(file)
    res = judge_handler.judge(config.root_path + config.temp_file + file)
    logger.error(str(res) + ' ' + file)
    if res:
        # messagebox.showinfo("提示", "1号机发现异常行为")
        shutil.move(config.root_path + config.temp_file + file, config.root_path + config.log_path + file)
    else:
        os.remove(config.root_path + config.temp_file + file)


def change_process(each_count):
    counts = get_count()
    # print(counts)
    threads = threading.enumerate()
    # logger.error(str(threads))
    normal_count = int(math.ceil(counts / float(each_count))) if int(math.ceil(counts / float(each_count))) > 0 else 1
    this_count = len(threads) - 1
    # print(threads)
    # print(normal_count, this_count)
    if normal_count > this_count:
        for i in range(normal_count - this_count):
            thread = threading.Thread(target=customer_thread)
            thread.start()
            # thread.join()
    elif normal_count < this_count - 1:
        cnt = 0  # this_count - normal_count
        for i in threads:
            if cnt >= this_count - normal_count:
                break
            if not i.is_alive():
                stop_thread(i)
                cnt += 1


def monitor_thread():
    # cnt = 0
    while True:
        try:
            change_process(300)
        except Exception as e:
            logger.error(str(e) + ' failed to change the consumers')
        time.sleep(config.monitor_time)
        # cnt += 1


def get_count():
    try:
        mq_conn = pika.BlockingConnection(
            pika.ConnectionParameters(config.queue_domain,
                                      credentials=pika.PlainCredentials(config.queue_user, config.queue_pwd)))
        chan = mq_conn.channel()
        queue = chan.queue_declare(queue=config.queue_name, durable=True)
    except Exception as e:
        logger.error(str(e) + ' can not set a server channel')
        return 0
    else:
        count = queue.method.message_count
        mq_conn.close()
        return count


if __name__ == '__main__':
    while True:
        try:
            change_process(config.each_count)
            print('[+] Judge server starts...')
            # print('test')
        except Exception as e:
            logger.error(str(e) + ' failed to change the consumers')
        time.sleep(config.monitor_time)
