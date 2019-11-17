import click
import tensorflow as tf

from estimator import model_fn
from utils import load_npy, LoggingLevels

config = tf.ConfigProto()
config.gpu_options.allow_growth = True


@click.group()
@click.option("--images",
              "-X",
              required=True,
              help="Path to .npy testing images file")
@click.option("--labels",
              "-y",
              required=True,
              help="Path to .npy testing labels file")
@click.option("--logging-level",
              "-l",
              default='ERROR',
              help="Logging verbosity level")
@click.option("--output-dir",
              "-o",
              default="./models",
              help="Path to desired checkpoint directory")
@click.option("--test-steps",
              "-t",
              default=10,
              help="Desired steps for testing")
@click.option("--batch-size",
              "-b",
              default=1,
              help="Desired batch size for training")
@click.option("--learning-rate",
              "-lr",
              default=1.0e-3,
              help="Initial learning rate for training")
@click.option("--epochs",
              "-e",
              default=20,
              help="Number of epochs to train for")
@click.option("--num-classes",
              "-nc",
              default=3,
              help="Number of classes for segmentation")
@click.pass_context
def cli(ctx, images, labels, logging_level, output_dir, test_steps, batch_size,
        learning_rate, epochs, num_classes):
    # Initialize logging and create folders
    tf.compat.v1.logging.set_verbosity(LoggingLevels[logging_level].value)
    tf.io.gfile.makedirs(output_dir)

    # Load data
    X = load_npy(images)
    y = load_npy(labels)

    # Build the Estimator
    model = tf.estimator.Estimator(
        model_fn=model_fn,
        model_dir=output_dir,
        config=tf.contrib.learn.RunConfig(session_config=config),
        params={
            'learning_rate': learning_rate,
            'num_classes': num_classes
        })

    # Pass X, y, and model through a click context
    ctx.obj = {
        'X': X,
        'y': y,
        'model': model,
        'batch_size': batch_size,
        'epochs': epochs,
        'test_steps': test_steps
    }


@cli.command(name="evaluate")
@click.pass_context
def evaluate(ctx):
    # Construct the input function
    input_fn = tf.compat.v1.estimator.inputs.numpy_input_fn(x=ctx.obj['X'],
                                                            y=ctx.obj['y'],
                                                            shuffle=False)

    # Evaluate the Model
    ctx.obj['model'].evaluate(input_fn, steps=ctx.obj['test_steps'])


@cli.command(name="predict")
@click.pass_context
def predict(ctx):
    # Construct the input function
    input_fn = tf.compat.v1.estimator.inputs.numpy_input_fn(x=ctx.obj['X'],
                                                            y=ctx.obj['y'],
                                                            shuffle=False)

    # Evaluate the Model
    for item in ctx.obj['model'].predict(input_fn):
        print(item)


@cli.command(name="train")
@click.pass_context
def train(ctx):
    # Define the input function for training
    input_fn = tf.compat.v1.estimator.inputs.numpy_input_fn(
        x=ctx.obj['X'],
        y=ctx.obj['y'],
        batch_size=ctx.obj['batch_size'],
        num_epochs=ctx.obj['epochs'],
        shuffle=True)

    # Train the Model
    num_train_steps = int(ctx.obj['X'].shape[0] // ctx.obj['batch_size'])
    ctx.obj['model'].train(input_fn, steps=num_train_steps)


if __name__ == '__main__':
    cli()
