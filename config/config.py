import os


class Config:
    queue_domain = 'localhost'
    queue_user = 'duke'
    queue_pwd = '123456'
    log_path = 'monitor_log/'
    temp_file = 'temp_file/'
    queue_name = 'monitor'
    root_path = './'
    monitor_time = 1 * 60
    each_count = 5
    online_wait = 5

    def __init__(self):
        os.makedirs(self.log_path, exist_ok=True)
        os.makedirs(self.temp_file, exist_ok=True)


config = Config()
