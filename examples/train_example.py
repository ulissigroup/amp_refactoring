import numpy as np
import torch
from ase import Atoms
from ase.calculators.emt import EMT

from amptorch.ase_utils import AMPtorch
from amptorch.trainer import AtomsTrainer

distances = np.linspace(2, 5, 100)
images = []
for dist in distances:
    image = Atoms(
        "CuCO",
        [
            (-dist * np.sin(0.65), dist * np.cos(0.65), 0),
            (0, 0, 0),
            (dist * np.sin(0.65), dist * np.cos(0.65), 0),
        ],
    )
    image.set_cell([10, 10, 10])
    image.wrap(pbc=True)
    image.set_calculator(EMT())
    images.append(image)


Gs = {
    "default": {
        "G2": {
            "etas": np.logspace(np.log10(0.05), np.log10(5.0), num=4),
            "rs_s": [0],
        },
        "G4": {"etas": [0.005], "zetas": [1.0, 4.0], "gammas": [1.0, -1.0]},
        "cutoff": 6,
    },
}

config = {
    "model": {
        "get_forces": True,
        "num_layers": 3,
        "num_nodes": 5,
        "batchnorm": False,
    },
    "optim": {
        "force_coefficient": 0.04,
        "lr": 1e-2,
        "batch_size": 32,
        "epochs": 100,
        "loss": "mse",
        "metric": "mae",
        "gpus": 0,
    },
    "dataset": {
        "raw_data": images,
        "val_split": 0.1,
        "fp_params": Gs,
        "save_fps": True,
        # feature scaling to be used - normalize or standardize
        # normalize requires a range to be specified
        "scaling": {"type": "normalize", "range": (0, 1)},
    },
    "cmd": {
        "debug": False,
        "run_dir": "./",
        "seed": 1,
        "identifier": "test",
        "verbose": True,
        # Weights and Biases used for logging - an account(free) is required
        "logger": False,
    },
}

config["dataset"]["cutoff_params"] = cosine_cutoff_params
torch.set_num_threads(1)
cosine_trainer = AtomsTrainer(config)
cosine_trainer.train()

predictions = cosine_trainer.predict(images)

true_energies = np.array([image.get_potential_energy() for image in images])
cosine_pred_energies = np.array(predictions["energy"])

image.set_calculator(AMPtorch(cosine_trainer))
image.get_potential_energy()


config["dataset"]["cutoff_params"] = polynomial_cutoff_params
torch.set_num_threads(1)
polynomial_trainer = AtomsTrainer(config)
polynomial_trainer.train()

predictions = polynomial_trainer.predict(images)

polynomial_pred_energies = np.array(predictions["energy"])

print("Energy MSE (Cosine):", np.mean((true_energies - cosine_pred_energies) ** 2))
print("Energy MAE (Cosine):", np.mean(np.abs(true_energies - cosine_pred_energies)))

print(
    "Energy MSE (Polynomial):", np.mean((true_energies - polynomial_pred_energies) ** 2)
)
print(
    "Energy MAE (Polynomial):",
    np.mean(np.abs(true_energies - polynomial_pred_energies)),
)

image.set_calculator(AMPtorch(polynomial_trainer))
image.get_potential_energy()
