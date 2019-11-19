import click
import cv2
import os
import numpy as np
import numpy.ma as ma
import sys


@click.group(chain=True)
def cli():
    pass

@cli.command(name="preview")
@click.option("--filename", "-f", required=True, help="Path to .npy file")
def preview(filename):
    data = np.load(filename)
    for index, image in enumerate(data):
        cv2.imshow("Image preview {}".format(index), image)
        k = cv2.waitKey(0)
        if k == 27:
            cv2.destroyAllWindows()
            exit()

@cli.command(name="compare")
@click.option("--filename1", "-f1", required=True, help="Path to .npy file")
@click.option("--filename2", "-f2", required=True, help="Path to .npy file")
def preview(filename1, filename2):
    data1 = np.load(filename1)
    data2 = np.load(filename2)
    for index, _ in enumerate(data1):
        cv2.imshow("File1 preview {}".format(index), data1[index])
        cv2.imshow("File2 preview {}".format(index), data2[index])
        k = cv2.waitKey(0)
        if k == 27:
            cv2.destroyAllWindows()
            exit()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    cli()
