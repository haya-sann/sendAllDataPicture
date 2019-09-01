import logging
def get_module_logger(modname):
    logger = logging.getLogger(modname)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(name)s] %(asctime)s %(levelname)s : %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # root権限に昇格
    if os.geteuid():
        args = [sys.executable] + sys.argv
        os.execlp(‘sudo’, ‘sudo’, *args)
    fileHandler = logging.FileHandler('/var/log/field_location.log', mode='a', encoding=None, delay=0)


    fileHandler.setFormatter(formatter)
    fileHandler.setLevel(logging.DEBUG)
    logger.addHandler(fileHandler)


    return logger

    