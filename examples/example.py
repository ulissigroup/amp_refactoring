"""An example of how to utilize the package to train on energies and forces"""

import sys
from ase import Atoms
import ase
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from amptorch.NN_model import CustomLoss, LogCoshLoss
from amptorch import AMP
from amptorch.core import AMPTorch
from amp.descriptor.gaussian import Gaussian

# define training images
IMAGES = "../datasets/water/water.extxyz"
images = ase.io.read(IMAGES, ":")
IMAGES = []
for i in range(100):
    IMAGES.append(images[i])

# define symmetry functions to be used
GSF = {}
GSF["G2_etas"] = np.logspace(np.log10(0.05), np.log10(5.0), num=4)
GSF["G2_rs_s"] = [0] * 4
GSF["G4_etas"] = [0.005]
GSF["G4_zetas"] = [1.0, 4.0]
GSF["G4_gammas"] = [1.0, -1]
GSF["cutoff"] = 6.5

# define the number of threads to parallelize training across
torch.set_num_threads(1)

# declare the calculator and corresponding model to be used
calc = AMP(
    model=AMPTorch(
        IMAGES,
        descriptor=Gaussian,
        Gs=GSF,
        cores=1,
        force_coefficient=0.3,
        lj_data=None,
        label='example',
        save_logs=False
    )
)
# define model settings
calc.model.structure = [3, 5]
calc.model.val_frac = 0.2
calc.model.epochs = 10
calc.model.structure = [5, 5]
calc.lr = 1
calc.criterion = CustomLoss
calc.optimizer = optim.LBFGS

# train the model
calc.train(overwrite=True)
