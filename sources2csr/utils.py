import json
import logging
import os

from .data_exception import DataException

logger = logging.getLogger(__name__)


def read_dict_from_file(filename, path=None):
    logger.debug('Reading json file {}'.format(filename))
    file = os.path.join(path, filename)
    if os.path.exists(file):
        try:
            with open(file, 'r') as f:
                dict_ = json.loads(f.read())
            return dict_
        except ValueError as ve:
            logger.error('JSON file {} had unexpected characters. {}'.format(filename, ve))
            raise DataException('JSON file {} had unexpected characters. {}'.format(filename, ve))
    else:
        logger.error('Expected config file: {} - not found. Aborting'.format(file))
        raise DataException('File not found: {}'.format(file))


def bool_is_file(filename, path):
    """If filename is not a file, has codebook in its name or starts with a . returns False, else True
    """
    path_ = os.path.join(path, filename)
    if 'codebook' in filename.lower():
        return False
    if filename.startswith('.'):
        return False

    return os.path.isfile(path_)


def get_filelist(dir_, skip=['NGS']):
    """

    :param dir_:
    :param skip: String value of files or
    :return:
    """
    file_list = []
    for filename in os.listdir(dir_):
        if filename.startswith('.') or filename in skip or 'codebook' in filename:
            continue
        file = os.path.join(dir_, filename)
        if os.path.isdir(file):
            file_list += get_filelist(file)
        elif bool_is_file(filename, dir_):
            file_list.append(file)
        else:
            logger.warning('{} in {} not a valid clinical file, skipping'.format(filename, file))
    return file_list
