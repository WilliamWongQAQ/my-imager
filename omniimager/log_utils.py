import logging
import logging.handlers
import os
import time
import yaml

from omniimager.params_parser import parser

LOG_LEVEL_DICT = {
    'CRITICAL': logging.CRITICAL,
    'FATAL': logging.FATAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'WARN': logging.WARN,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG
}


class LogUtils(logging.Logger):

    def __init__(self, name):
        # 设置收集器： （本质就是拿到一个父类Logger的对象）
        super().__init__(name)
        parsed_args = parser.parse_args()
        with open(parsed_args.config_file, 'r') as config_file:
            config_options = yaml.load(config_file, Loader=yaml.SafeLoader)
        log_level = config_options.get('log_level', 'DEBUG')
        if log_level in LOG_LEVEL_DICT.keys():
            log_level = LOG_LEVEL_DICT.get(log_level)
        else:
            log_level = LOG_LEVEL_DICT.get('DEBUG')
        log_dir = config_options.get('log_dir', '/var/log/omni-imager')
        # set log levels
        # LEVELS = {'NOSET': logging.NOTSET,
        #           'DEBUG': logging.DEBUG,
        #           'INFO': logging.INFO,
        #           'WARNING': logging.WARNING,
        #           'ERROR': logging.ERROR,
        #           'CRITICAL': logging.CRITICAL}

        if not (os.path.exists(log_dir) and os.path.isdir(log_dir)):
            os.makedirs(log_dir)

        date = time.strftime("%Y-%m-%d", time.localtime())
        logfile_name = f'{date}.log'
        logfile_path = os.path.join(log_dir, logfile_name)
        rotatingFileHandler = logging.handlers.RotatingFileHandler(filename=logfile_path,
                                                                   maxBytes=1024 * 1024 * 50,
                                                                   backupCount=5)
        formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)s]%(message)s',
                                      '%Y-%m-%d %H:%M:%S')
        rotatingFileHandler.setFormatter(formatter)

        console = logging.StreamHandler()
        console.setLevel(log_level)
        console.setFormatter(formatter)
        self.addHandler(rotatingFileHandler)
        self.addHandler(console)
        self.setLevel(log_level)


logger = LogUtils('logger')
