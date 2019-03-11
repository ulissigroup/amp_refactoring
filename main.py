import sys
import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader
from data import AtomsDataset,data_factorization,collate_amp
from amp.descriptor.gaussian import Gaussian
from nn_torch import FullNN,train_model
import torch.optim as optim
from torch.optim import lr_scheduler

from ase.build import molecule
from ase import Atoms
from ase.calculators.emt import EMT

device=torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

training_data=AtomsDataset('water.extxyz',descriptor=Gaussian())
unique_atoms,_,_,_=data_factorization(training_data)
n_unique_atoms=len(unique_atoms)

validation_frac=.1
samplers=training_data.data_split(training_data,validation_frac)
dataset_sizes={'train':(1.-validation_frac)*len(training_data),'val':validation_frac*len(training_data)}

atoms_dataloaders={x:DataLoader(training_data,batch_size=100,collate_fn=collate_amp,sampler=samplers[x],pin_memory=True)
        for x in ['train','val']}
model=FullNN(unique_atoms)
model=model.to(device)
criterion=nn.MSELoss()

#Define the optimizer and implement any optimization settings
optimizer_ft=optim.SGD(model.parameters(),lr=.01,momentum=0.9)
# optimizer_ft=optim.SGD(model.parameters(),lr=.001)

#Define scheduler search strategies
exp_lr_scheduler=lr_scheduler.StepLR(optimizer_ft,step_size=20,gamma=0.1)

model=train_model(model,unique_atoms,dataset_sizes,criterion,optimizer_ft,exp_lr_scheduler,atoms_dataloaders,num_epochs=100)

torch.save(model.state_dict(),'benchmark_dataset/benchmark_model.pt')

def test_model():
    model=FullNN(unique_atoms)
    model=model.to(device)
    model.load_state_dict(torch.load('Atomistic_model.pt'))

    for data_sample in atoms_dataloader:
        outputs,target=model(data_sample)
        print outputs
        print target
        print('')
