from enum import Enum
import numpy as np
import tensorflow as tf


class LoggingLevels(Enum):
    DEBUG = tf.compat.v1.logging.DEBUG
    ERROR = tf.compat.v1.logging.ERROR
    FATAL = tf.compat.v1.logging.FATAL
    INFO = tf.compat.v1.logging.INFO
    WARN = tf.compat.v1.logging.WARN


def load_npy(filename):
    assert filename.endswith(".npy"), tf.logging.ERROR(
        "Expected .npy file as input.")
    try:
        loaded = np.load(filename)
    except IOError as e:
        tf.logging.ERROR("File does not exist or cannot be read.")
        raise e
    except ValueError as e:
        raise e
    return loaded
