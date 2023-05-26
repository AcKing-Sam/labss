import logging

def config_log():

    # 获取logger
    logger = logging.getLogger('fuzzing')

    LOG_FORMAT = "%(asctime)s \n%(message)s"
    DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"

    # 部署时log
    deploy_handler = logging.FileHandler('logs/deploy.log', 'w')
    # 执行时log
    execute_handler = logging.FileHandler('logs/execute.log', 'w')

    deploy_handler.setFormatter(logging.Formatter(
        fmt = LOG_FORMAT,
        datefmt = DATE_FORMAT
    ))

    execute_handler.setFormatter(logging.Formatter(
        fmt = LOG_FORMAT,
        datefmt = DATE_FORMAT
    ))

    info_filter = logging.Filter()
    info_filter.filter = lambda record: record.levelno == logging.INFO
    warning_filter = logging.Filter()
    warning_filter.filter = lambda record: record.levelno == logging.WARNING

    deploy_handler.addFilter(info_filter)
    execute_handler.addFilter(warning_filter)

    logger.addHandler(deploy_handler)
    logger.addHandler(execute_handler)

    logger.setLevel('INFO')

    return logger


if __name__ == '__main__':
    logger = config_log()

    logger.info('info')
    logger.warning('warning')