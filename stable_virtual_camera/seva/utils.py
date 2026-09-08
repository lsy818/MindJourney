from scripts.p1_svc_assets import validated_asset_digest
import os

import safetensors.torch
import torch
from huggingface_hub import hf_hub_download

from stable_virtual_camera.seva.model import Seva, SevaParams


def seed_everything(seed: int = 0):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def print_load_warning(missing: list[str], unexpected: list[str]) -> None:
    if len(missing) > 0 and len(unexpected) > 0:
        print(f"Got {len(missing)} missing keys:\n\t" + "\n\t".join(missing))
        print("\n" + "-" * 79 + "\n")
        print(f"Got {len(unexpected)} unexpected keys:\n\t" + "\n\t".join(unexpected))
    elif len(missing) > 0:
        print(f"Got {len(missing)} missing keys:\n\t" + "\n\t".join(missing))
    elif len(unexpected) > 0:
        print(f"Got {len(unexpected)} unexpected keys:\n\t" + "\n\t".join(unexpected))


def load_model(
    pretrained_model_name_or_path: str = "stabilityai/stable-virtual-camera",
    weight_name: str = "model.safetensors",
    device: str | torch.device = "cuda",
    verbose: bool = False,
) -> Seva:
    revision = os.environ.get("SVC_REVISION")
    if os.path.isdir(pretrained_model_name_or_path):
        weight_path = os.path.join(pretrained_model_name_or_path, weight_name)
    else:
        config_path = hf_hub_download(
            repo_id=pretrained_model_name_or_path,
            filename="config.yaml",
            revision=revision,
        )
        weight_path = hf_hub_download(
            repo_id=pretrained_model_name_or_path,
            filename=weight_name,
            revision=revision,
        )
        if verbose:
            print(f"Using pinned SVC config: {config_path}")

    expected_sha256 = os.environ.get("SVC_WEIGHT_SHA256")
    if expected_sha256:
        actual_sha256 = validated_asset_digest(weight_path, expected_sha256)
        if actual_sha256 != expected_sha256:
            raise RuntimeError(
                f"SVC checkpoint SHA256 mismatch: expected {expected_sha256}, "
                f"found {actual_sha256}."
            )

    state_dict = safetensors.torch.load_file(
        weight_path,
        device=str(device),
    )

    with torch.device("meta"):
        model = Seva(SevaParams()).to(torch.bfloat16)

    missing, unexpected = model.load_state_dict(state_dict, strict=False, assign=True)
    if verbose:
        print_load_warning(missing, unexpected)
    if os.environ.get("SVC_STRICT_LOAD", "0") == "1" and (missing or unexpected):
        raise RuntimeError(
            "SVC checkpoint is incompatible with the released architecture: "
            f"{len(missing)} missing and {len(unexpected)} unexpected keys."
        )
    return model
