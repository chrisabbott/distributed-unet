import tensorflow as tf


class UNet:
    def __init__(self, input_tensor, num_classes):
        self.classes = num_classes
        self.model = self._model(input_tensor)

    def _maxpool2d(self, X, kernel, stride, name='maxpool2d'):
        with tf.compat.v1.variable_scope(name):
            return tf.nn.max_pool2d(
                input=X,
                ksize=[1, kernel, kernel, 1],
                strides=[1, stride, stride, 1],
                padding='SAME')

    def _conv2d(self, X, filters, kernel, stride, name='conv2d'):
        with tf.compat.v1.variable_scope(name):
            filters = tf.Variable(
                tf.random.normal([kernel, kernel, X.shape[-1], filters]))
            X = tf.nn.conv2d(
                input=X,
                filters=filters,
                strides=[stride, stride],
                padding='VALID')
            biases = tf.Variable(tf.random.normal([X.shape[-1]]))
            X = tf.nn.bias_add(X, biases)
            return tf.nn.relu(X)

    def _conv2d_transpose(self, X, filters, kernel, stride, factor=2, name='conv2d_transpose'):
        with tf.compat.v1.variable_scope(name):
            filters = tf.Variable(
                tf.random.normal([kernel, kernel, X.shape[-1], filters]))
            X = tf.nn.conv2d_transpose(
                input=X,
                filters=filters,
                output_shape=[
                    X.shape[0],
                    X.shape[1] * factor,
                    X.shape[2] * factor,
                    X.shape[-1] // factor],
                strides=[stride, stride],
                padding='VALID')
            biases = tf.Variable(tf.random.normal([X.shape[-1]]))
            X = tf.nn.bias_add(X, biases)
            return tf.nn.relu(X)

    def _crop_concat(self, A, B, name='crop_concat'):
        with tf.compat.v1.variable_scope(name):
            crop_height = abs(int(A.shape[1]) - int(B.shape[1]))
            crop_width = abs(int(A.shape[2]) - int(B.shape[2]))
            X = tf.image.crop_to_bounding_box(
                image=A,
                offset_height=crop_height // 2,
                offset_width=crop_width // 2,
                target_height=int(B.shape[1]),
                target_width=int(B.shape[2]))
            return tf.concat([X, B], axis=-1)

    def _model(self, input_tensor):
        with tf.compat.v1.variable_scope('UNet'):
            with tf.compat.v1.variable_scope('ContractingPath'):
                with tf.compat.v1.variable_scope('ContractingBlock_0'):
                    conv0 = self._conv2d(input_tensor, filters=64, kernel=3, stride=1)
                    conv0 = self._conv2d(conv0, filters=64, kernel=3, stride=1)
                    pool0 = self._maxpool2d(conv0, kernel=2, stride=2)
                with tf.compat.v1.variable_scope('ContractingBlock_1'):
                    conv1 = self._conv2d(pool0, filters=128, kernel=3, stride=1)
                    conv1 = self._conv2d(conv1, filters=128, kernel=3, stride=1)
                    pool1 = self._maxpool2d(conv1, kernel=2, stride=2)
                with tf.compat.v1.variable_scope('ContractingBlock_2'):
                    conv2 = self._conv2d(pool1, filters=256, kernel=3, stride=1)
                    conv2 = self._conv2d(conv2, filters=256, kernel=3, stride=1)
                    pool2 = self._maxpool2d(conv2, kernel=2, stride=2)
                with tf.compat.v1.variable_scope('ContractingBlock_3'):
                    conv3 = self._conv2d(pool2, filters=512, kernel=3, stride=1)
                    conv3 = self._conv2d(conv3, filters=512, kernel=3, stride=1)
                    pool3 = self._maxpool2d(conv3, kernel=2, stride=2)
            with tf.compat.v1.variable_scope('Bridge'):
                conv4 = self._conv2d(pool3, filters=1024, kernel=3, stride=1)
                conv4 = self._conv2d(conv4, filters=1024, kernel=3, stride=1)
            with tf.compat.v1.variable_scope('ExpansivePath'):
                with tf.compat.v1.variable_scope('ExpansiveBlock_0'):
                    conv5 = self._conv2d_transpose(conv4, filters=512, kernel=2, stride=1)
                    skip5 = self._crop_concat(conv3, conv5)
                    conv5 = self._conv2d(skip5, filters=512, kernel=3, stride=1)
                    conv5 = self._conv2d(conv5, filters=512, kernel=3, stride=1)
                with tf.compat.v1.variable_scope('ExpansiveBlock_1'):
                    conv6 = self._conv2d_transpose(conv5, filters=256, kernel=2, stride=1)
                    skip6 = self._crop_concat(conv2, conv6)
                    conv6 = self._conv2d(skip6, filters=256, kernel=3, stride=1)
                    conv6 = self._conv2d(conv6, filters=256, kernel=3, stride=1)
                with tf.compat.v1.variable_scope('ExpansiveBlock_2'):
                    conv7 = self._conv2d_transpose(conv6, filters=128, kernel=2, stride=1)
                    skip7 = self._crop_concat(conv1, conv7)
                    conv7 = self._conv2d(skip7, filters=128, kernel=3, stride=1)
                    conv7 = self._conv2d(conv7, filters=128, kernel=3, stride=1)
                with tf.compat.v1.variable_scope('ExpansiveBlock_3'):
                    conv8 = self._conv2d_transpose(conv7, filters=64, kernel=2, stride=1)
                    skip8 = self._crop_concat(conv0, conv8)
                    conv8 = self._conv2d(skip8, filters=64, kernel=3, stride=1)
                    conv8 = self._conv2d(conv8, filters=64, kernel=3, stride=1)
                    conv8 = self._conv2d(conv8, filters=self.classes, kernel=1, stride=1)
                    return conv8


def main():
    batch_size = 1
    img_size = 572
    img_dims = 3
    X = tf.compat.v1.placeholder(dtype=tf.float32, shape=(batch_size, img_size, img_size, img_dims))
    net = UNet(input_tensor=X, num_classes=4).model


if __name__ == '__main__':
    main()
