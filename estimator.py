import tensorflow as tf

from modeling import UNet


def model_fn(features, labels, mode, params):
    logits_train = UNet(features, params['num_classes'],
                        is_training=True).model
    logits_test = UNet(features, params['num_classes'],
                       is_training=False).model
    predictions_train = tf.one_hot(indices=tf.argmax(logits_train, axis=-1),
                                   depth=params['num_classes'])
    predictions_test = tf.one_hot(indices=tf.argmax(logits_test, axis=-1),
                                  depth=params['num_classes'])

    loss_op = tf.reduce_mean(
        tf.nn.sparse_softmax_cross_entropy_with_logits(labels=tf.argmax(
            labels, axis=-1), logits=logits_train))
    optimizer = tf.train.AdamOptimizer(learning_rate=params['learning_rate'])
    train_op = optimizer.minimize(loss_op,
                                  global_step=tf.train.get_global_step())

    acc_op = tf.metrics.accuracy(labels=labels, predictions=predictions_test)

    estim_specs = tf.estimator.EstimatorSpec(
        mode=mode,
        predictions=(predictions_test if mode == tf.estimator.ModeKeys.EVAL else
                     predictions_train),
        loss=loss_op,
        train_op=train_op,
        eval_metric_ops={'accuracy': acc_op})
    return estim_specs
