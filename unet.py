import click
import tensorflow as tf
import horovod.tensorflow as hvd

from estimator import model_fn
from utils import load_npy, LoggingLevels


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
              default=1.0e-4,
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
    # Initialize horovod
    hvd.init()
    
    # One GPU per process
    config = tf.compat.v1.ConfigProto()
    config.gpu_options.allow_growth = True
    config.gpu_options.visible_device_list = str(hvd.local_rank())
    
    # Initialize logging and create folders
    tf.compat.v1.logging.set_verbosity(LoggingLevels[logging_level].value)
    tf.io.gfile.makedirs(output_dir)

    # Load data
    X = load_npy(images)
    y = load_npy(labels)

    # Build the Estimator
    model = tf.estimator.Estimator(
        model_fn=model_fn,
        model_dir=output_dir if hvd.rank() == 0 else None,
        config=tf.contrib.learn.RunConfig(session_config=config),
        params={
            'learning_rate': learning_rate,
            'num_classes': num_classes
        })

    # Broadcasts variable state from worker 0 to workers 1..n
    broadcast_hook = hvd.BroadcastGlobalVariablesHook(0)

    # Pass X, y, and model through a click context
    ctx.obj = {
        'X': X,
        'y': y,
        'model': model,
        'batch_size': batch_size,
        'epochs': epochs,
        'test_steps': test_steps,
        'broadcast_hook': broadcast_hook
    }


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
    train_input_fn = tf.compat.v1.estimator.inputs.numpy_input_fn(
        x=ctx.obj['X'],
        y=ctx.obj['y'],
        batch_size=ctx.obj['batch_size'],
        num_epochs=ctx.obj['epochs'],
        shuffle=True)

    # Train the Model
    num_train_steps = int(ctx.obj['epochs']) * int(
        ctx.obj['X'].shape[0] // ctx.obj['batch_size'])
    ctx.obj['model'].train(input_fn=train_input_fn,
                           steps=num_train_steps // hvd.size(),
                           hooks=[ctx.obj['broadcast_hook']])


@cli.command(name="train-and-evaluate")
@click.pass_context
def train_and_evaluate(ctx):
    # Construct the input function
    train_input_fn = tf.compat.v1.estimator.inputs.numpy_input_fn(
        x=ctx.obj['X'],
        y=ctx.obj['y'],
        batch_size=ctx.obj['batch_size'],
        num_epochs=ctx.obj['epochs'],
        shuffle=True)
    eval_input_fn = tf.compat.v1.estimator.inputs.numpy_input_fn(
        x=ctx.obj['X'], y=ctx.obj['y'], shuffle=False)

    # Train and evaluate the Model
    num_train_steps = int(ctx.obj['epochs']) * int(
        ctx.obj['X'].shape[0] // ctx.obj['batch_size'])
    tf.estimator.train_and_evaluate(
        estimator=ctx.obj['model'],
        train_spec=tf.estimator.TrainSpec(input_fn=train_input_fn,
                                          max_steps=num_train_steps),
        eval_spec=tf.estimator.EvalSpec(input_fn=eval_input_fn))


if __name__ == '__main__':
    cli()
