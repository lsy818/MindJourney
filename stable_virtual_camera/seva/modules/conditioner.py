from scripts.p1_svc_assets import validated_asset_digest
import os

import kornia
import open_clip
import torch
from huggingface_hub import hf_hub_download
from torch import nn


class CLIPConditioner(nn.Module):
    mean: torch.Tensor
    std: torch.Tensor

    def __init__(self):
        super().__init__()
        clip_repo = os.environ.get(
            "SVC_OPENCLIP_REPO", "laion/CLIP-ViT-H-14-laion2B-s32B-b79K"
        )
        clip_revision = os.environ.get(
            "SVC_OPENCLIP_REVISION", "1c2b8495b28150b8a4922ee1c8edee224c284c0c"
        )
        clip_filename = os.environ.get(
            "SVC_OPENCLIP_FILENAME", "open_clip_pytorch_model.bin"
        )
        clip_path = hf_hub_download(
            repo_id=clip_repo,
            filename=clip_filename,
            revision=clip_revision,
        )
        expected_sha256 = os.environ.get(
            "SVC_OPENCLIP_SHA256",
            "9a78ef8e8c73fd0df621682e7a8e8eb36c6916cb3c16b291a082ecd52ab79cc4",
        )
        actual_sha256 = validated_asset_digest(clip_path, expected_sha256)
        if actual_sha256 != expected_sha256:
            raise RuntimeError(
                "OpenCLIP checkpoint SHA256 mismatch: "
                f"expected {expected_sha256}, found {actual_sha256}."
            )
        self.module = open_clip.create_model_and_transforms(
            "ViT-H-14", pretrained=clip_path
        )[0]
        self.module.eval().requires_grad_(False)  # type: ignore
        self.register_buffer(
            "mean", torch.Tensor([0.48145466, 0.4578275, 0.40821073]), persistent=False
        )
        self.register_buffer(
            "std", torch.Tensor([0.26862954, 0.26130258, 0.27577711]), persistent=False
        )

    def preprocess(self, x: torch.Tensor) -> torch.Tensor:
        x = kornia.geometry.resize(
            x,
            (224, 224),
            interpolation="bicubic",
            align_corners=True,
            antialias=True,
        )
        x = (x + 1.0) / 2.0
        x = kornia.enhance.normalize(x, self.mean, self.std)
        return x

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.preprocess(x)
        x = self.module.encode_image(x)
        return x
