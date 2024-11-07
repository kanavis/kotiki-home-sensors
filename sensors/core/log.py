import logging


def setup_logging(debug: bool):
    level = logging.DEBUG if debug else logging.INFO
    log = logging.getLogger()
    log.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)
