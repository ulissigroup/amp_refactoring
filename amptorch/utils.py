import skorch
from skorch.utils import to_numpy
from torch_geometric.data import Batch
from torch.nn.parallel.scatter_gather import gather


def target_extractor(y):
    extracted = []
    for batch in y:
        energy_targets = to_numpy(batch[0])
        if len(batch) == 2:
            force_targets = to_numpy(batch[1])
            extracted.append([energy_targets, force_targets])
        elif len(batch) == 1:
            extracted.append([energy_targets, None])
    return extracted


def to_tensor(X, device, accept_sparse=False):
    if isinstance(X[0], Batch):
        return X
    else:
        for i, batch in enumerate(X):
            for j, targets in enumerate(batch):
                X[i][j] = targets.to(device)
        if device != "cpu":
            outputs = gather(X, device)
        else:
            outputs = X[0]
        return outputs


class train_end_load_best_loss(skorch.callbacks.base.Callback):
    def __init__(self, filename):
        self.filename = filename

    def on_train_end(self, net, X, y):
        net.load_params("./checkpoints/{}/params.pt".format(self.filename))
