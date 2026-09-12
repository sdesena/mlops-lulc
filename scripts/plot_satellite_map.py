"""Gera um mapa da ROI com imagem de satélite real como fundo (não altera run_pipeline.py)."""

from __future__ import annotations

import argparse
from pathlib import Path

import contextily as ctx
import matplotlib.pyplot as plt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/processed/roi_satellite_map.png"))
    parser.add_argument("--roi", nargs=4, type=float, metavar=("LON_MIN", "LAT_MIN", "LON_MAX", "LAT_MAX"), default=(-46.20, -7.70, -45.85, -7.35))
    parser.add_argument("--provider", default="Esri.WorldImagery", help="Provedor de tiles do contextily (ex.: Esri.WorldImagery)")
    return parser.parse_args()


def resolve_provider(name: str):
    # Navega o dicionário aninhado de providers do contextily a partir de um nome tipo "Esri.WorldImagery"
    provider = ctx.providers
    for part in name.split("."):
        provider = provider[part]
    return provider


def main() -> None:
    args = parse_args()
    lon_min, lat_min, lon_max, lat_max = args.roi

    figure, axis = plt.subplots(figsize=(8, 8))
    axis.set_xlim(lon_min, lon_max)
    axis.set_ylim(lat_min, lat_max)

    # mantém o eixo em EPSG:4326 (lat/lon) para exibir as coordenadas diretamente nos ticks
    ctx.add_basemap(axis, source=resolve_provider(args.provider), crs="EPSG:4326")

    axis.set_title("Área de estudo")
    axis.set_xlabel("Longitude")
    axis.set_ylabel("Latitude")
    figure.tight_layout()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=150)
    plt.close(figure)
    print(f"Mapa salvo em: {args.output}")


if __name__ == "__main__":
    main()