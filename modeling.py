import tensorflow as tf


class UNet:
    def __init__(self, input_tensor, num_classes, is_training):
        self.classes = num_classes
        self.is_training = is_training
        self.model = self._model(input_tensor)

    def _maxpool2d(self, input_tensor, kernel, stride, name="maxpool2d"):
        with tf.compat.v1.variable_scope(name):
            return tf.nn.max_pool2d(
                input=input_tensor,
                ksize=[1, kernel, kernel, 1],
                strides=[1, stride, stride, 1],
                padding="SAME",
            )

    def _conv2d(
            self,
            input_tensor,
            filters,
            kernel,
            stride,
            padding="SAME",
            activation=tf.nn.tanh,
            name="conv2d",
    ):
        with tf.compat.v1.variable_scope(name):
            _, _, _, channels = tf.unstack(tf.compat.v1.shape(input_tensor))
            filter = tf.Variable(
                tf.truncated_normal(
                    shape=[kernel, kernel, int(input_tensor.shape[3]), filters],
                    stddev=0.1))
            X = tf.nn.conv2d(
                input=input_tensor,
                filter=filter,
                strides=[1, stride, stride, 1],
                padding=padding,
            )
            biases = tf.Variable(tf.random.normal([int(X.shape[-1])]))
            activated = activation(tf.nn.bias_add(X, biases))
            return tf.compat.v1.layers.batch_normalization(activated)

    def _conv2d_transpose(
            self,
            input_tensor,
            filters,
            kernel,
            stride,
            factor=2,
            padding="SAME",
            activation=tf.nn.tanh,
            name="conv2d_transpose",
    ):
        with tf.compat.v1.variable_scope(name):
            # conv2d_transpose needs a static batch size
            batch_size, _, _, channels = tf.unstack(
                tf.compat.v1.shape(input_tensor))
            filter = tf.Variable(
                tf.truncated_normal(
                    shape=[kernel, kernel, filters, int(input_tensor.shape[3])],
                    stddev=0.1))
            X = tf.nn.conv2d_transpose(
                input=input_tensor,
                filters=filter,
                output_shape=[
                    batch_size,
                    int(input_tensor.shape[1]) * factor,
                    int(input_tensor.shape[2]) * factor,
                    int(input_tensor.shape[3]) // factor,
                ],
                strides=[1, stride, stride, 1],
                padding=padding,
            )
            biases = tf.Variable(tf.random.normal([int(X.shape[-1])]))
            activated = activation(tf.nn.bias_add(X, biases))
            return tf.compat.v1.layers.batch_normalization(activated)

    def _crop_concat(self, A, B, name="crop_concat"):
        with tf.compat.v1.variable_scope(name):
            crop_height = abs(int(A.shape[1]) - int(B.shape[1]))
            crop_width = abs(int(A.shape[2]) - int(B.shape[2]))
            X = tf.image.crop_to_bounding_box(
                image=A,
                offset_height=crop_height // 2,
                offset_width=crop_width // 2,
                target_height=int(B.shape[1]),
                target_width=int(B.shape[2]),
            )
            return tf.concat([X, B], axis=-1)

    def _model(self, input_tensor):
        batch_size = tf.shape(input_tensor)
        with tf.compat.v1.variable_scope("UNet"):
            with tf.compat.v1.variable_scope("ContractingPath"):
                with tf.compat.v1.variable_scope("ContractingBlock_0"):
                    conv0 = self._conv2d(input_tensor,
                                         filters=64,
                                         kernel=3,
                                         stride=1,
                                         name="conv0_0")
                    conv0 = self._conv2d(conv0,
                                         filters=64,
                                         kernel=3,
                                         stride=1,
                                         name="conv0_1")
                    pool0 = self._maxpool2d(conv0,
                                            kernel=2,
                                            stride=2,
                                            name="pool0_2")
                with tf.compat.v1.variable_scope("ContractingBlock_1"):
                    conv1 = self._conv2d(pool0,
                                         filters=128,
                                         kernel=3,
                                         stride=1,
                                         name="conv1_0")
                    conv1 = self._conv2d(conv1,
                                         filters=128,
                                         kernel=3,
                                         stride=1,
                                         name="conv1_1")
                    pool1 = self._maxpool2d(conv1,
                                            kernel=2,
                                            stride=2,
                                            name="pool1_2")
                with tf.compat.v1.variable_scope("ContractingBlock_2"):
                    conv2 = self._conv2d(pool1,
                                         filters=256,
                                         kernel=3,
                                         stride=1,
                                         name="conv2_0")
                    conv2 = self._conv2d(conv2,
                                         filters=256,
                                         kernel=3,
                                         stride=1,
                                         name="conv2_1")
                    pool2 = self._maxpool2d(conv2,
                                            kernel=2,
                                            stride=2,
                                            name="conv2_2")
                with tf.compat.v1.variable_scope("ContractingBlock_3"):
                    conv3 = self._conv2d(pool2,
                                         filters=512,
                                         kernel=3,
                                         stride=1,
                                         name="conv3_0")
                    conv3 = self._conv2d(conv3,
                                         filters=512,
                                         kernel=3,
                                         stride=1,
                                         name="conv3_1")
                    pool3 = self._maxpool2d(conv3,
                                            kernel=2,
                                            stride=2,
                                            name="conv3_2")
            with tf.compat.v1.variable_scope("Bridge"):
                conv4 = self._conv2d(pool3,
                                     filters=1024,
                                     kernel=3,
                                     stride=1,
                                     name="conv4_0")
                conv4 = self._conv2d(conv4,
                                     filters=1024,
                                     kernel=3,
                                     stride=1,
                                     name="conv4_1")
            with tf.compat.v1.variable_scope("ExpansivePath"):
                with tf.compat.v1.variable_scope("ExpansiveBlock_0"):
                    conv5 = self._conv2d_transpose(conv4,
                                                   filters=512,
                                                   kernel=1,
                                                   stride=2,
                                                   name="convt5_0")
                    skip5 = self._crop_concat(conv3, conv5, name="crop5_1")
                    conv5 = self._conv2d(skip5,
                                         filters=512,
                                         kernel=3,
                                         stride=1,
                                         name="conv5_2")
                    conv5 = self._conv2d(conv5,
                                         filters=512,
                                         kernel=3,
                                         stride=1,
                                         name="conv5_3")
                with tf.compat.v1.variable_scope("ExpansiveBlock_1"):
                    conv6 = self._conv2d_transpose(conv5,
                                                   filters=256,
                                                   kernel=1,
                                                   stride=2,
                                                   name="convt6_0")
                    skip6 = self._crop_concat(conv2, conv6, name="crop6_1")
                    conv6 = self._conv2d(skip6,
                                         filters=256,
                                         kernel=3,
                                         stride=1,
                                         name="conv6_2")
                    conv6 = self._conv2d(conv6,
                                         filters=256,
                                         kernel=3,
                                         stride=1,
                                         name="conv6_3")
                with tf.compat.v1.variable_scope("ExpansiveBlock_2"):
                    conv7 = self._conv2d_transpose(conv6,
                                                   filters=128,
                                                   kernel=1,
                                                   stride=2,
                                                   name="convt7_0")
                    skip7 = self._crop_concat(conv1, conv7, name="crop7_1")
                    conv7 = self._conv2d(skip7,
                                         filters=128,
                                         kernel=3,
                                         stride=1,
                                         name="conv7_2")
                    conv7 = self._conv2d(conv7,
                                         filters=128,
                                         kernel=3,
                                         stride=1,
                                         name="conv7_3")
                with tf.compat.v1.variable_scope("ExpansiveBlock_3"):
                    conv8 = self._conv2d_transpose(conv7,
                                                   filters=64,
                                                   kernel=1,
                                                   stride=2,
                                                   name="convt8_0")
                    skip8 = self._crop_concat(conv0, conv8, name="crop8_1")
                    conv8 = self._conv2d(skip8,
                                         filters=64,
                                         kernel=3,
                                         stride=1,
                                         name="conv8_2")
                    conv8 = self._conv2d(conv8,
                                         filters=64,
                                         kernel=3,
                                         stride=1,
                                         name="conv8_3")
                    return self._conv2d(
                        conv8,
                        filters=self.classes,
                        kernel=1,
                        stride=1,
                        name="conv8_4",
                    )
