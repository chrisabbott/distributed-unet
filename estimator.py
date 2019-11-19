import tensorflow as tf
import horovod.tensorflow as hvd

from modeling import UNet


def modified_dice_loss(labels, logits):
    eps = 1e-5
    predictions = tf.nn.softmax(logits)
    labels = tf.cast(labels, dtype=tf.float32)
    intersection = tf.reduce_sum(predictions * labels)
    union = eps + tf.reduce_sum(predictions) + tf.reduce_sum(labels)
    loss = -(2 * intersection / (union))
    return loss


def model_fn(features, labels, mode, params):
    logits = UNet(features,
                  params['num_classes'],
                  is_training=(mode == tf.estimator.ModeKeys.TRAIN)).model
    loss_op = tf.reduce_mean(modified_dice_loss(labels=labels, logits=logits))
    optimizer = tf.train.AdamOptimizer(learning_rate=params['learning_rate'] *
                                       hvd.size())

    optimizer = hvd.DistributedOptimizer(optimizer)
    hooks = [hvd.BroadcastGlobalVariablesHook(0)]

    train_op = optimizer.minimize(loss_op,
                                  global_step=tf.train.get_global_step())
    predictions = tf.one_hot(indices=tf.argmax(logits, axis=-1),
                             depth=params['num_classes'])
    tf.summary.image("Predictions", predictions, max_outputs=3)
    tf.summary.image("Labels", labels, max_outputs=3)
    tf.summary.image("Images", features, max_outputs=3)

    if mode == tf.estimator.ModeKeys.EVAL:
        acc_op = tf.metrics.accuracy(labels=labels, predictions=predictions)
        return tf.estimator.EstimatorSpec(mode=mode,
                                          loss=loss_op,
                                          eval_metric_ops={'accuracy': acc_op})
    elif mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions)
    elif mode == tf.estimator.ModeKeys.TRAIN:
        return tf.estimator.EstimatorSpec(mode=mode,
                                          predictions=predictions,
                                          loss=loss_op,
                                          train_op=train_op)
