import click
import cv2
from larcv import larcv
import numpy as np
import ROOT
from ROOT import TChain


@click.group(chain=True)
def cli():
    pass


@cli.command(name="preview")
@click.option("--filename", "-f", help="Path to .root file")
@click.option("--channel", "-c", help="Channel name")
def preview(filename, channel):
    # Create TChain for data image
    chain_image2d = ROOT.TChain('image2d_data_tree')
    chain_image2d.AddFile(filename)

    # Create TChain for label image2d_data_tree
    chain_label2d = ROOT.TChain('image2d_segment_tree')
    chain_label2d.AddFile(filename)

    entry = -1
    if entry < 0:
        entry = np.random.randint(0, chain_label2d.GetEntries())

    chain_label2d.GetEntry(entry)
    chain_image2d.GetEntry(entry)

    image2d = larcv.as_ndarray(chain_image2d.image2d_data_branch.as_vector().front())
    label2d = larcv.as_ndarray(chain_label2d.image2d_segment_branch.as_vector().front())

    cv2.imshow("Image preview", image2d)
    cv2.waitKey(0)
    cv2.imshow("Segmentation preview", label2d)
    cv2.waitKey(0)


if __name__ == '__main__':
    cli()
