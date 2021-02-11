import torch

try:
    shell = get_ipython().__class__.__name__
    if shell == "ZMQInteractiveShell":
        from tqdm.notebook import tqdm
    else:
        from tqdm import tqdm
except NameError:
    from tqdm import tqdm


class FeatureScaler:
    """
    Normalizes an input tensor and later reverts it.
    Adapted from https://github.com/Open-Catalyst-Project/baselines
    """

    def __init__(
        self,
        data_list,
        forcetraining,
        scaling,
    ):
        self.transform = scaling["type"]
        if self.transform not in ["normalize", "standardize"]:
            raise NotImplementedError(f"{self.transform} scaling not supported.")
        if self.transform == "normalize" and "range" not in scaling:
            raise NotImplementedError("Normalization requires desire range.")
        if self.transform == "normalize":
            feature_range = scaling["range"]
        self.forcetraining = forcetraining
        fingerprints = torch.cat([data.fingerprint for data in data_list], dim=0)
        atomic_numbers = torch.cat([data.atomic_numbers for data in data_list], dim=0)
        self.unique = torch.unique(atomic_numbers).tolist()
        self.scales = {}
        for element in self.unique:
            idx = torch.where(atomic_numbers == element)[0]
            element_fps = fingerprints[idx]
            if self.transform == "standardize":
                mean = torch.mean(element_fps, dim=0)
                std = torch.std(element_fps, dim=0, unbiased=False)
                std[std < 1e-8] = 1
                self.scales[element] = {"offset": mean, "scale": std}
            else:
                fpmin = torch.min(element_fps, dim=0).values
                fpmax = torch.max(element_fps, dim=0).values
                data_range = fpmax - fpmin
                data_range[data_range < 1e-8] = 1
                scale = (feature_range[1] - feature_range[0]) / (data_range)
                offset = feature_range[0] - fpmin * scale
                self.scales[element] = {"offset": offset, "scale": scale}

    def norm(self, data_list, disable_tqdm=False):
        for data in tqdm(
            data_list,
            desc="Scaling Feature data (%s)" % self.transform,
            total=len(data_list),
            unit=" scalings",
            disable=disable_tqdm,
        ):
            fingerprint = data.fingerprint
            atomic_numbers = data.atomic_numbers
            for element in self.unique:
                element_idx = torch.where(atomic_numbers == element)
                element_fp = fingerprint[element_idx]
                if self.transform == "standardize":
                    element_fp = (
                        element_fp - self.scales[element]["offset"]
                    ) / self.scales[element]["scale"]
                else:
                    element_fp = (
                        element_fp * self.scales[element]["scale"]
                    ) + self.scales[element]["offset"]
                fingerprint[element_idx] = element_fp
            if self.forcetraining:
                base_atoms = torch.repeat_interleave(
                    atomic_numbers, data.fingerprint.shape[1]
                )
                fp_idx = data.fprimes._indices()[0]
                fp_idx_to_scale = fp_idx % data.fingerprint.shape[1]
                element_idx = base_atoms[fp_idx].tolist()
                _values = data.fprimes._values()

                dict_elements = {element: [] for element in set(element_idx)}
                for i, element in enumerate(element_idx):
                    dict_elements[element].append(i)

                for element, ids in dict_elements.items():
                    scale = self.scales[element]["scale"][fp_idx_to_scale[ids]]
                    if self.transform == "standardize":
                        _values[ids] /= scale
                    else:
                        _values[ids] *= scale

                _indices = data.fprimes._indices()
                _size = data.fprimes.size()
                data.fprimes = torch.sparse.FloatTensor(_indices, _values, _size)
        return data_list


class TargetScaler:
    """
    Normalizes an input tensor and later reverts it.
    Adapted from https://github.com/Open-Catalyst-Project/baselines
    """

    def __init__(self, data_list, forcetraining):
        self.forcetraining = forcetraining

        energies = torch.tensor([data.energy for data in data_list])
        self.target_mean = torch.mean(energies, dim=0)
        self.target_std = torch.std(energies, dim=0)

        if torch.isnan(self.target_std) or self.target_std == 0:
            self.target_mean = 0
            self.target_std = 1

    def norm(self, data_list, disable_tqdm=False):
        for data in tqdm(
            data_list,
            desc="Scaling Target data",
            total=len(data_list),
            unit=" scalings",
            disable=disable_tqdm,
        ):
            data.energy = (data.energy - self.target_mean) / self.target_std

            if self.forcetraining:
                data.forces /= self.target_std
        return data_list

    def denorm(self, tensor, pred="energy"):
        if pred == "energy":
            tensor = (tensor * self.target_std) + self.target_mean
        elif pred == "forces":
            tensor = tensor * self.target_std

        return tensor


def sparse_block_diag(arrs):
    # TODO CUDA support
    r = []
    c = []
    v = []
    dim_1, dim_2 = 0, 0
    for k, mtx in enumerate(arrs):
        r += [mtx._indices()[0] + dim_1]
        c += [mtx._indices()[1] + dim_2]
        v += [mtx._values()]
        dim_1 += mtx.shape[0]
        dim_2 += mtx.shape[1]
    r = torch.cat(r, dim=0)
    c = torch.cat(c, dim=0)
    _indices = torch.stack([r, c])
    _values = torch.cat(v)
    _shapes = [dim_1, dim_2]
    out = torch.sparse.DoubleTensor(_indices, _values, _shapes)

    return out
