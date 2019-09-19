import logging.config
import os

import yaml


def setup_logging(debug: bool):
    """
    Setup logging configuration
    :param debug: flag if debug messages should be displayed
    :param name: application name to write the log for
    """
    default_level = logging.DEBUG if debug else logging.INFO
    path = os.environ.get('LOG_CFG', 'csr/logging.yaml')
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        config['root']['level'] = default_level
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)
