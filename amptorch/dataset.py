from torch.utils.data import Dataset
from torch_geometric.data import Batch

from amptorch.descriptor.Gaussian import Gaussian
from amptorch.descriptor.MCSH import AtomisticMCSH
from amptorch.preprocessing import (
    AtomsToData,
    FeatureScaler,
    TargetScaler,
    sparse_block_diag,
)


class AtomsDataset(Dataset):
    def __init__(
        self,
        images,
        descriptor_setup,
        forcetraining=True,
        save_fps=True,
        scaling={"type": "normalize", "range": (0, 1)},
        cores=1,
    ):
        self.images = images
        self.forcetraining = forcetraining
        self.scaling = scaling
        fp_scheme, fp_params, cutoff_params, elements = descriptor_setup
        if fp_scheme == "gaussian":
            self.descriptor = Gaussian(Gs=fp_params, elements=elements, **cutoff_params)
        elif fp_scheme == "mcsh":
            self.descriptor = AtomisticMCSH(MCSHs=fp_params, elements=elements)
        else:
            raise NotImplementedError

        self.a2d = AtomsToData(
            descriptor=self.descriptor,
            r_energy=True,
            r_forces=self.forcetraining,
            save_fps=save_fps,
            fprimes=forcetraining,
            cores=cores,
        )

        self.data_list = self.process()

    def process(self):
        data_list = self.a2d.convert_all(self.images)

        self.feature_scaler = FeatureScaler(data_list, self.forcetraining, self.scaling)
        self.target_scaler = TargetScaler(data_list, self.forcetraining)
        self.feature_scaler.norm(data_list)
        self.target_scaler.norm(data_list)

        return data_list

    @property
    def input_dim(self):
        return self.data_list[0].fingerprint.shape[1]

    def __len__(self):
        return len(self.data_list)

    def __getitem__(self, index):
        return self.data_list[index]


class DataCollater:
    def __init__(self, train=True, forcetraining=True):
        self.train = train
        self.forcetraining = forcetraining

    def __call__(self, data_list):
        if self.forcetraining:
            mtxs = []
            for data in data_list:
                mtxs.append(data.fprimes)
                data.fprimes = None
            batch = Batch.from_data_list(data_list)
            for i, data in enumerate(data_list):
                data.fprimes = mtxs[i]
            block_matrix = sparse_block_diag(mtxs)
            batch.fprimes = block_matrix
        else:
            batch = Batch.from_data_list(data_list)

        if self.train:
            if self.forcetraining:
                return batch, [batch.energy, batch.forces]
            else:
                return batch, [
                    batch.energy,
                ]
        else:
            return batch
