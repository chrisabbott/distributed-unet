import tensorflow as tf

from modeling import UNet


def model_fn(features, labels, mode, params):
    logits_train = UNet(features, params['num_classes'], is_training=True).model
    logits_test = UNet(features, params['num_classes'], is_training=False).model

    predictions_test = tf.one_hot(
        indices=tf.argmax(logits_test, axis=-1), depth=params['num_classes'])

    if mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(mode, predictions=predictions_test)

    #loss_op = tf.reduce_mean(tf.nn.sparse_softmax_cross_entropy_with_logits(
    #    logits=logits_train, labels=tf.cast(labels, dtype=tf.int32)))
    #cce = tf.keras.losses.CategoricalCrossentropy()
    #loss_op = cce(y_true=tf.cast(labels, dtype=tf.int32),
    #              y_pred=tf.nn.softmax(logits_train))
    #loss_op = tf.reduce_mean(
    #    tf.losses.softmax_cross_entropy(onehot_labels=labels, logits=logits_train))
    loss_op = tf.reduce_mean(
        tf.nn.sparse_softmax_cross_entropy_with_logits(
            labels=tf.argmax(labels, axis=-1), logits=logits_train))
    optimizer = tf.train.AdamOptimizer(learning_rate=params['learning_rate'])
    train_op = optimizer.minimize(loss_op, global_step=tf.train.get_global_step())

    acc_op = tf.metrics.accuracy(labels=labels, predictions=predictions_test)

    estim_specs = tf.estimator.EstimatorSpec(
        mode=mode,
        predictions=predictions_test,
        loss=loss_op,
        train_op=train_op,
        eval_metric_ops={'accuracy': acc_op})
    return estim_specs
