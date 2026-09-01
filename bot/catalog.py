"""Реестр платных продуктов — единая точка правды для цены/названия/кода."""
from __future__ import annotations

from dataclasses import dataclass

from . import texts
from .config import Config


@dataclass(frozen=True)
class Product:
    code: str
    title: str
    price_rub: int
    description: str


def build_catalog(cfg: Config) -> dict[str, Product]:
    return {
        "1": Product("1", texts.PRODUCT1_TITLE, cfg.product1_price_rub, texts.PRODUCT1_DESCRIPTION),
        "2": Product("2", texts.PRODUCT2_TITLE, cfg.product2_price_rub, texts.PRODUCT2_DESCRIPTION),
    }
