import tensorflow as tf

from modeling import UNet


def model_fn(features, labels, mode, params):
    logits = UNet(features, params['num_classes'],
                  is_training=(mode == tf.estimator.ModeKeys.TRAIN)).model
    loss_op = tf.reduce_mean(
      tf.nn.sparse_softmax_cross_entropy_with_logits(labels=tf.argmax(
         labels, axis=-1), logits=logits))
    optimizer = tf.train.AdamOptimizer(learning_rate=params['learning_rate'])
    train_op = optimizer.minimize(loss_op,
                                  global_step=tf.train.get_global_step())
    predictions = tf.one_hot(indices=tf.argmax(logits, axis=-1),
                             depth=params['num_classes'])
    tf.summary.image("Predictions", predictions, max_outputs=3)
    tf.summary.image("Labels", labels, max_outputs=3)

    if mode == tf.estimator.ModeKeys.EVAL:
        acc_op = tf.metrics.accuracy(labels=labels, predictions=predictions)
        return tf.estimator.EstimatorSpec(
            mode=mode,
            loss=loss_op,
            eval_metric_ops={'accuracy': acc_op}
        )
    elif mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(
            mode=mode,
            predictions=predictions
        )
    elif mode == tf.estimator.ModeKeys.TRAIN:
        return tf.estimator.EstimatorSpec(
            mode=mode,
            predictions=predictions,
            loss=loss_op,
            train_op=train_op
        )
