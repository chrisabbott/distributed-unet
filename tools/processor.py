import click
import cv2
from larcv import larcv
import os
import numpy as np
import numpy.ma as ma
import ROOT
from ROOT import TChain
import sys

np.set_printoptions(threshold=sys.maxsize)


@click.group(chain=True)
def cli():
    pass

@cli.command(name="root-to-npy")
@click.option("--filename", "-i", required=True, help="Path to .root file")
def root_to_npy(filename):
    basename = os.path.splitext(filename)[0]

    # Create TChain for data image
    chain_image2d = ROOT.TChain('image2d_data_tree')
    chain_image2d.AddFile(filename)

    # Create TChain for label image2d_data_tree
    chain_label2d = ROOT.TChain('image2d_segment_tree')
    chain_label2d.AddFile(filename)

    _X = []
    _y = []

    for sample in range(chain_image2d.GetEntries()):
        chain_image2d.GetEntry(sample)
        image = np.copy(
            larcv.as_ndarray(
                chain_image2d.image2d_data_branch.as_vector().front()))
        _X.append(image)

    X = np.reshape(np.stack(_X, axis=0),
                   (len(_X), _X[0].shape[0], _X[0].shape[1], 1))
    print("Saving X ...")
    print("X.shape = {}".format(X.shape))
    np.save("{}_X.npy".format(basename), X)

    for sample in range(chain_label2d.GetEntries()):
        chain_label2d.GetEntry(sample)
        label = larcv.as_ndarray(
            chain_label2d.image2d_segment_branch.as_vector().front())
        _label = []
        for class_index in range(3):
            _label.append(
                np.multiply(np.ones_like(label),
                            (label == class_index).astype(int)))
        __label = (np.stack(_label, axis=-1))
        _y.append(__label.astype(np.uint8) * 255)

    y = np.reshape(np.stack(_y, axis=0),
                   (len(_y), _y[0].shape[0], _y[0].shape[1], 3))
    print("Saving y ...")
    print("y.shape: {}".format(y.shape))
    np.save("{}_y.npy".format(basename), y)


if __name__ == '__main__':
    cli()
