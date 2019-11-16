import click
import numpy as np
import sys
import tensorflow as tf

from estimator import model_fn
from utils import load_npy, LoggingLevels


@click.group(chain=True)
def cli():
    pass


@cli.command(name="train")
@click.option("--images", "-X", required=True,
              help="Path to .npy training images file")
@click.option("--labels", "-y", required=True,
              help="Path to .npy training labels file")
@click.option("--logging-level", "-l", default='INFO',
              help="Logging verbosity level")
@click.option("--output-dir", "-o", default="./",
              help="Path to desired checkpoint directory")
@click.option("--batch-size", "-b", default=1,
              help="Desired batch size for training")
@click.option("--epochs", "-e", default=20,
              help="Number of epochs to train for")
@click.option("--learning-rate", "-lr", default=1.0e-4,
              help="Initial learning rate for training")
@click.option("--num-classes", "-nc", default=3,
              help="Number of classes for segmentation")
def train(images, labels, logging_level, output_dir, batch_size, epochs, learning_rate, num_classes):
    # Initialize logging and create folders
    tf.compat.v1.logging.set_verbosity(LoggingLevels[logging_level].value)
    tf.io.gfile.makedirs(output_dir)

    # Load data
    train_X = load_npy(images)
    train_y = load_npy(labels)
    num_train_steps = int(train_X.shape[0] // batch_size)

    # Build the Estimator
    model = tf.estimator.Estimator(
        model_fn=model_fn,
        model_dir=output_dir,
        params={'learning_rate': learning_rate,
                'num_classes': num_classes})

    # Define the input function for training
    input_fn = tf.compat.v1.estimator.inputs.numpy_input_fn(
        x=train_X, y=train_y,
        batch_size=batch_size, num_epochs=epochs, shuffle=True)

    # Train the Model
    model.train(input_fn, steps=num_train_steps)


if __name__ == '__main__':
    cli()
