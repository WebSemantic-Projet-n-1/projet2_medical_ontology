#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitaire device : priorite CUDA, repli CPU.

STRUCTURE
---------
- get_device() : retourne "cuda" (ou "cuda:0") si torch.cuda.is_available(), sinon "cpu".
- Utiliser ce device pour tout calcul PyTorch (tensors, modeles) afin de beneficier du GPU
  quand il est disponible, sans changer le code sur une machine sans CUDA.

Usage dans les scripts d'analyse ou le service web :
  from util.device import get_device
  device = get_device()
  tensor = tensor.to(device)
"""

try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


def get_device() -> str:
    """
    Retourne le device a utiliser : CUDA en priorite, sinon CPU.
    Si PyTorch n'est pas installe, retourne "cpu" (les appels .to(device) devront etre evites ou conditionnes).
    """
    if not _TORCH_AVAILABLE:
        return "cpu"
    return "cuda" if torch.cuda.is_available() else "cpu"


def is_cuda_available() -> bool:
    """Indique si CUDA est disponible (PyTorch installe et GPU detecte)."""
    if not _TORCH_AVAILABLE:
        return False
    return torch.cuda.is_available()
