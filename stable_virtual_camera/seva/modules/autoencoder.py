import hashlib
import os

import torch
from diffusers.models import AutoencoderKL  # type: ignore
from huggingface_hub import hf_hub_download
from torch import nn


class AutoEncoder(nn.Module):
    scale_factor: float = 0.18215
    downsample: int = 8

    def __init__(self, chunk_size: int | None = None):
        super().__init__()
        repo_id = os.environ.get(
            "SVC_VAE_REPO", "stabilityai/stable-diffusion-2-1-base"
        )
        revision = os.environ.get("SVC_VAE_REVISION")
        subfolder = os.environ.get("SVC_VAE_SUBFOLDER", "vae") or None
        expected_sha256 = os.environ.get("SVC_VAE_SHA256")

        if expected_sha256:
            filename = "diffusion_pytorch_model.safetensors"
            if subfolder:
                filename = f"{subfolder}/{filename}"
            weight_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                revision=revision,
            )
            digest = hashlib.sha256()
            with open(weight_path, "rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(block)
            actual_sha256 = digest.hexdigest()
            if actual_sha256 != expected_sha256:
                raise RuntimeError(
                    "VAE weight SHA256 mismatch: "
                    f"expected {expected_sha256}, found {actual_sha256}."
                )

        self.module = AutoencoderKL.from_pretrained(
            repo_id,
            revision=revision,
            subfolder=subfolder,
            use_safetensors=True,
            force_download=False,
            low_cpu_mem_usage=False,
        )
        self.module.eval().requires_grad_(False)  # type: ignore
        self.chunk_size = chunk_size

    def _encode(self, x: torch.Tensor) -> torch.Tensor:
        return (
            self.module.encode(x).latent_dist.mean  # type: ignore
            * self.scale_factor
        )

    def encode(self, x: torch.Tensor, chunk_size: int | None = None) -> torch.Tensor:
        chunk_size = chunk_size or self.chunk_size
        if chunk_size is not None:
            return torch.cat(
                [self._encode(x_chunk) for x_chunk in x.split(chunk_size)],
                dim=0,
            )
        else:
            return self._encode(x)

    def _decode(self, z: torch.Tensor) -> torch.Tensor:
        return self.module.decode(z / self.scale_factor).sample  # type: ignore

    def decode(self, z: torch.Tensor, chunk_size: int | None = None) -> torch.Tensor:
        chunk_size = chunk_size or self.chunk_size
        if chunk_size is not None:
            return torch.cat(
                [self._decode(z_chunk) for z_chunk in z.split(chunk_size)],
                dim=0,
            )
        else:
            return self._decode(z)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decode(self.encode(x))
