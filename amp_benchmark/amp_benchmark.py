from amp import Amp
from amp.descriptor.gaussian import Gaussian
from amp.model.neuralnetwork import NeuralNetwork
from amp.model import LossFunction
from amp import analysis
import ase
from ase import io

calc = Amp(descriptor=Gaussian(), model=NeuralNetwork(), label="calc")
calc.model.lossfunction = LossFunction(convergence={'energy_rmse':0.02,'force_rmse':0.02})
images = ase.io.read("water.extxyz", ":")
calc.train(images)
analysis.plot_parity("calc.amp", images)
