"""Run the small SITS + MLflow LULC experiment from a terminal."""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
import time
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import mlflow
import pandas as pd
from shapely.geometry import box

from pysits import (
    sits_classify,
    sits_cube,
    sits_get_data,
    sits_kfold_validate,
    sits_label_classification,
    sits_rfor,
    sits_smooth,
    sits_timeline,
    sits_train,
)

LOG = logging.getLogger("mlops_lulc")

TERRA_CLASS_COLORS = {
    "VEGETACAO_NATURAL_PRIMARIA": "#005500",
    "VEGETACAO_NATURAL_SECUNDARIA": "#0FC80F",
    "SILVICULTURA": "#A8A800",
    "PASTAGEM": "#FFEC87",
    "CULTURA_AGRICOLA_PERENE": "#FF8828",
    "CULTURA_AGRICOLA_SEMIPERENE": "#996400",
    "CULTURA_AGRICOLA_TEMPORARIA_DE_1_CICLO": "#FFE300",
    "CULTURA_AGRICOLA_TEMPORARIA_DE_MAIS_DE_1_CICLO": "#FFFF00",
    "MINERACAO": "#AD89CD",
    "URBANIZADA": "#FFA8C0",
    "OUTROS_USOS": "#E1E1E1",
    "OUTRAS_AREAS_EDIFICADAS": "#FF00C5",
    "DESFLORESTAMENTO_NO_ANO": "#FF0000",
    "CORPO_DAGUA": "#0000FF",
    "NAO_OBSERVADO": "#FFFFFF",
}


def parse_args() -> argparse.Namespace:
    # Define e faz o parsing de todos os argumentos de linha de comando do experimento
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shapefile", type=Path, required=True)  # shapefile com os polígonos de referência (ex.: TerraClass)
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))  # diretório onde tudo será salvo
    parser.add_argument("--tracking-uri", default="http://localhost:5000")  # endereço do servidor MLflow
    parser.add_argument("--experiment", default="sits-terraclass-balsas-v2")  # nome do experimento no MLflow
    parser.add_argument("--run-name", default="baseline")  # nome desta execução específica
    parser.add_argument("--start-date", default="2024-01-01")  # início da série temporal
    parser.add_argument("--end-date", default="2024-03-30")  # fim da série temporal
    parser.add_argument("--n-points-per-class", type=int, default=10)  # nº de pontos amostrados por polígono
    parser.add_argument("--num-trees", type=int, default=20)  # nº de árvores do Random Forest
    parser.add_argument("--roi", nargs=4, type=float, metavar=("LON_MIN", "LAT_MIN", "LON_MAX", "LAT_MAX"), default=(-46.20, -7.70, -45.85, -7.35))  # recorte espacial (bounding box)
    parser.add_argument("--bands", nargs="+", default=["NDVI"])  # bandas/índices a serem usados no cubo
    parser.add_argument("--classes", nargs="+", help="Classes TerraClass a incluir")  # filtro opcional de classes
    parser.add_argument("--folds", type=int, default=5)  # nº de folds na validação cruzada
    parser.add_argument("--run-classification", action="store_true")  # se True, roda a classificação completa do cubo (etapa mais pesada)
    return parser.parse_args()


def sample_polygons(gdf: gpd.GeoDataFrame, n_points: int, start_date: str, end_date: str) -> pd.DataFrame:
    # Para cada polígono do GeoDataFrame, sorteia n_points pontos internos e monta
    # uma linha por ponto com coordenadas, rótulo (classe) e o intervalo temporal desejado
    # rng fixo por polígono garante que a mesma amostra seja reproduzida entre execuções
    rows = []
    for _, feature in gdf.iterrows():
        points = gpd.GeoSeries([feature.geometry], crs="EPSG:4326").sample_points(n_points, rng=42).iloc[0]
        for point in points.geoms:
            rows.append({
                "longitude": point.x,
                "latitude": point.y,
                "label": feature["CLASSE"],
                "start_date": start_date,
                "end_date": end_date,
            })
    return pd.DataFrame(rows)


def save_series_plot(time_series: pd.DataFrame, path: Path) -> None:
    # Gera e salva um gráfico com as séries temporais de NDVI das primeiras 30 amostras
    # plota só NDVI mesmo em runs multibanda, para manter o gráfico legível
    figure, axis = plt.subplots(figsize=(10, 5))
    for _, row in time_series.head(30).iterrows():
        series = row["time_series"]
        if "NDVI" not in series:
            continue
        axis.plot(series.index, series["NDVI"], alpha=0.35, color="steelblue")
    axis.set_title("NDVI das séries temporais amostradas")
    axis.set_xlabel("Data")
    axis.set_ylabel("NDVI")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def save_sample_map(gdf: gpd.GeoDataFrame, samples: pd.DataFrame, path: Path) -> None:
    # Gera um mapa colorido (paleta oficial do TerraClass) dos polígonos da área de estudo
    # sobrepostos com os pontos de amostra extraídos, em preto para contraste com qualquer cor de fundo
    figure, axis = plt.subplots(figsize=(8, 8))
    for classe, group in gdf.groupby("CLASSE"):
        color = TERRA_CLASS_COLORS.get(classe, "#CCCCCC")  # cinza como fallback para classes fora do dicionário
        group.plot(ax=axis, color=color, edgecolor="0.3", linewidth=0.3, label=classe)
    axis.scatter(
        samples["longitude"], samples["latitude"],
        s=25, marker="x", color="black", linewidths=1.5, zorder=5,
    )
    axis.set_title("Amostras TerraClass na ROI")
    axis.set_xlabel("Longitude")
    axis.set_ylabel("Latitude")
    axis.legend(loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=8, title="Classe")
    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)

def parse_kfold_metrics(result: object) -> dict[str, float]:
    # Extrai métricas (Accuracy, Kappa) do resultado de sits_kfold_validate via regex,
    # já que o pysits devolve o resultado como texto formatado em R, sem acesso estruturado às métricas
    text = str(result)
    metrics = {}
    for name in ("Accuracy", "Kappa"):
        match = re.search(rf"{name}\s*:\s*([0-9.]+)", text)
        if match:
            metrics[name.lower()] = float(match.group(1))
    return metrics


def command_output(command: list[str], default: str = "unavailable") -> str:
    # Executa um comando de shell e retorna sua saída como string, sem propagar exceção;
    # usado para capturar versão do pysits e commit git sem quebrar a run se algo faltar
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return default


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    started = time.perf_counter()  # marca o início total da execução, para medir o tempo decorrido no final

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    # subpastas criadas mesmo sem --run-classification, para manter a estrutura de saída estável
    for directory in ("probs", "bayes", "classified"):
        (output_dir / directory).mkdir(exist_ok=True)

    # Monta o dicionário de configuração/parâmetros da run (usado tanto para salvar em disco
    # quanto para logar como parâmetros no MLflow)
    lon_min, lat_min, lon_max, lat_max = args.roi
    roi = {"lon_min": lon_min, "lat_min": lat_min, "lon_max": lon_max, "lat_max": lat_max}
    config = {
        "collection": "SENTINEL-2-16D",
        "bands": args.bands,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "roi": roi,
        "n_points_per_class": args.n_points_per_class,
        "classes": json.dumps(args.classes) if args.classes else "all",  # lista serializada: MLflow só aceita parâmetros escalares
        "num_trees": args.num_trees,
        "folds": args.folds,
        "seed": 42,
        "python_version": sys.version.split()[0],
        "pysits_version": command_output([sys.executable, "-c", "import importlib.metadata; print(importlib.metadata.version('pysits'))"]),
        "git_commit": command_output(["git", "rev-parse", "HEAD"]),
    }
    (output_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    # ---- Etapa de preparação: carrega o shapefile, recorta pela ROI, filtra classes e amostra pontos ----
    preparation_started = time.perf_counter()
    gdf = gpd.read_file(args.shapefile).to_crs("EPSG:4326")
    study_area = gpd.clip(gdf, box(lon_min, lat_min, lon_max, lat_max))
    if args.classes:
        # Valida que todas as classes pedidas via --classes realmente existem na área recortada
        missing_classes = sorted(set(args.classes) - set(study_area["CLASSE"]))
        if missing_classes:
            raise ValueError(f"Classes não encontradas na ROI: {missing_classes}")
        study_area = study_area[study_area["CLASSE"].isin(args.classes)].copy()
    if study_area.empty:
        raise ValueError("Nenhuma classe disponível após o recorte da ROI")

    # Amostra pontos dentro dos polígonos e persiste os artefatos intermediários em disco
    samples = sample_polygons(study_area, args.n_points_per_class, args.start_date, args.end_date)
    samples.to_csv(output_dir / "samples.csv", index=False)
    study_area[["CLASSE", "geometry"]].to_file(output_dir / "study_area.geojson", driver="GeoJSON")
    study_area["CLASSE"].value_counts().rename("count").to_csv(output_dir / "class_distribution.csv")
    save_sample_map(study_area, samples, output_dir / "samples_map.png")
    preparation_seconds = time.perf_counter() - preparation_started

    # ---- Configuração do MLflow: aponta para o servidor de tracking e define o experimento ----
    mlflow.set_tracking_uri(args.tracking_uri)
    mlflow.set_experiment(args.experiment)
    with mlflow.start_run(run_name=args.run_name) as run:
        # Registra metadados, parâmetros e os arquivos de entrada/preparação já gerados
        mlflow.set_tags({"project": "mlops-lulc", "region": "balsas-ma", "reference": "terraclass-2024"})
        mlflow.log_params({**config, "bands": ",".join(args.bands), "roi": json.dumps(roi)})
        mlflow.log_artifacts(str(output_dir), artifact_path="inputs")

        # ---- Construção do cubo de dados (SITS) a partir da coleção Sentinel-2 no BDC ----
        cube_started = time.perf_counter()
        cube = sits_cube(
            source="BDC",
            collection="SENTINEL-2-16D",
            bands=args.bands,
            start_date=args.start_date,
            end_date=args.end_date,
            roi=roi,
            multicores=2,  # >1 core historicamente estourou a memória do WSL2 nesta máquina
        )
        timeline = sits_timeline(cube)
        LOG.info("Timeline: %s", timeline)
        cube_seconds = time.perf_counter() - cube_started

        # ---- Extração das séries temporais nos pontos amostrados a partir do cubo ----
        extraction_started = time.perf_counter()
        time_series = sits_get_data(cube=cube, samples=samples, multicores=2)
        save_series_plot(time_series, output_dir / "time_series.png")
        time_series[["longitude", "latitude", "label", "start_date", "end_date"]].to_csv(
            output_dir / "time_series_metadata.csv", index=False
        )
        extraction_seconds = time.perf_counter() - extraction_started

        # ---- Validação cruzada (k-fold) do modelo Random Forest sobre as séries temporais ----
        validation_started = time.perf_counter()
        kfold = sits_kfold_validate(
            samples=time_series,
            folds=args.folds,
            ml_method=sits_rfor(num_trees=args.num_trees),
            multicores=2,
        )
        (output_dir / "kfold_result.txt").write_text(str(kfold), encoding="utf-8")
        LOG.info("Validação retornou %s", type(kfold))
        kfold_metrics = parse_kfold_metrics(kfold)  # extrai accuracy/kappa do texto retornado
        (output_dir / "kfold_metrics.json").write_text(
            json.dumps(kfold_metrics, indent=2), encoding="utf-8"
        )
        if kfold_metrics:
            mlflow.log_metrics(kfold_metrics)
        mlflow.log_artifact(str(output_dir / "kfold_result.txt"), artifact_path="metrics")
        mlflow.log_artifact(str(output_dir / "kfold_metrics.json"), artifact_path="metrics")
        validation_seconds = time.perf_counter() - validation_started

        # ---- Treinamento final do modelo com todas as séries temporais disponíveis ----
        training_started = time.perf_counter()
        model = sits_train(samples=time_series, ml_method=sits_rfor(num_trees=args.num_trees))
        mlflow.log_param("trained", True)
        training_seconds = time.perf_counter() - training_started
        elapsed_seconds = time.perf_counter() - started

        # Monta um resumo da execução (contagens, tempos de cada etapa) e salva/loga no MLflow
        summary = {
            "run_id": run.info.run_id,
            "n_samples": len(samples),
            "n_classes": int(samples["label"].nunique()),
            "n_dates": len(timeline),
            "elapsed_seconds": elapsed_seconds,
            "classification_requested": args.run_classification,
            "preparation_seconds": preparation_seconds,
            "cube_seconds": cube_seconds,
            "extraction_seconds": extraction_seconds,
            "validation_seconds": validation_seconds,
            "training_seconds": training_seconds,
        }
        (output_dir / "run_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
        mlflow.log_metrics(
            {
                "n_samples": summary["n_samples"],
                "n_classes": summary["n_classes"],
                "n_dates": summary["n_dates"],
                "elapsed_seconds": elapsed_seconds,
                "preparation_seconds": preparation_seconds,
                "cube_seconds": cube_seconds,
                "extraction_seconds": extraction_seconds,
                "validation_seconds": validation_seconds,
                "training_seconds": training_seconds,
            }
        )
        mlflow.log_artifact(str(output_dir / "run_summary.json"), artifact_path="metrics")
        mlflow.log_artifacts(str(output_dir), artifact_path="artifacts")  # loga novamente tudo o que está em output_dir, já incluindo os arquivos gerados até aqui

        # ---- Etapa opcional: classificação completa do cubo (probabilidades -> suavização Bayesiana -> rotulação) ----
        if args.run_classification:
            probs_cube = sits_classify(
                data=cube,
                ml_model=model,
                output_dir=str(output_dir / "probs"),
                multicores=2,
                memsize=2,  # classifica todo o cubo (todos os pixels da ROI); mantém baixo para não travar o WSL2
                progress=True,
            )
            bayes_cube = sits_smooth(
                cube=probs_cube,
                output_dir=str(output_dir / "bayes"),
                multicores=2,
                progress=True,
            )
            label_cube = sits_label_classification(
                cube=bayes_cube,
                output_dir=str(output_dir / "classified"),
                progress=True,
            )
            (output_dir / "classification_summary.txt").write_text(str(label_cube), encoding="utf-8")
            mlflow.log_artifacts(str(output_dir / "classified"), artifact_path="classified_map")

        LOG.info("MLflow run: %s", run.info.run_id)


if __name__ == "__main__":
    main()