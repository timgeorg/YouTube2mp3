import logging, sys

class Logger:
    logger: logging.Logger = None

    def create_logger(self, log_level) -> logging.Logger:
        if self.logger is not None:
            return self.logger
        
        log: logging.Logger = logging.getLogger(f"{self.__class__.__name__}")
        log.setLevel(log_level)

        handler: logging.StreamHandler = logging.StreamHandler(sys.stdout)
        formatter: logging.Formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        log.addHandler(handler)
        handler: logging.FileHandler = logging.FileHandler(f"{self.__class__.__name__}.log")
        formatter: logging.Formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        log.addHandler(handler)
        self.logger = log
