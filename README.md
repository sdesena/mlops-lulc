# MLOps para Classificação de Uso e Cobertura da Terra (LULC)

Pipeline de MLOps aplicado à classificação LULC com séries temporais de imagens de satélite:

- **Amostras**: TerraClass 2024 (vetorial), recortadas para uma área de estudo na fronteira agrícola do Maranhão (região de Balsas)
- **Dados de satélite**: cubos do [Brazil Data Cube](https://data.inpe.br/bdc/) (Sentinel-2, coleção `SENTINEL-2-16D`) via STAC
- **Modelagem**: [SITS](https://e-sensing.github.io/sitsbook/) (Satellite Image Time Series) via [pysits](https://github.com/e-sensing/pysits)
- **MLOps**: tracking de experimentos e registro de artefatos com MLflow

## Arquitetura de infraestrutura

Infraestrutura minimalista, sem orquestrador de workflows — adequada a ambientes com recursos limitados:

```
Docker (1 container)
└─ MLflow :5000          # tracking + artifact store (SQLite + volume local)

Ambiente mamba (mlops_lulc)
├─ Jupyter Lab           # desenvolvimento interativo
├─ Python + pysits
└─ R + sits              # o pysits é um wrapper do pacote R sits
```

## Requisitos

- Linux (ou Windows com WSL2)
- Docker + Docker Compose
- [Miniforge/Mambaforge](https://github.com/conda-forge/miniforge) (mamba)
- ~8 GB de RAM livres (o SITS carrega uma sessão R embutida via rpy2)

## Setup

### 1. Clonar e criar o ambiente

```bash
git clone https://github.com/sdesena/mlops-lulc.git
cd mlops-lulc
mamba env create          # lê environment.yml (inclui R, r-sits, pysits)
mamba activate mlops_lulc
```

Se o ambiente já existir e o `environment.yml` tiver mudado:

```bash
mamba env update -n mlops_lulc -f environment.yml
```

Validação rápida do binding R ↔ Python (etapa mais frágil do setup):

```bash
R -e "library(arrow); library(sits); print(packageVersion('sits'))"
python -c "from pysits import *; print('pysits OK')"
```

### 2. Subir o MLflow

```bash
docker compose up -d
docker ps   # deve mostrar mlops_lulc-mlflow-1 na porta 5000
```

UI do MLflow: http://localhost:5000. Experimentos e artefatos persistem em `mlflow_data/` (não versionado).

### 3. Dados de entrada

Baixe o TerraClass 2024 (vetorial, `.V`) do [portal TerraClass](http://www.terraclass.gov.br/) e coloque em `data/`:

```
data/CER.2024.MARANHAO.21.V/CER.2024.MARANHAO.21.V.shp
```

Os dados brutos não são versionados (ver `.gitignore`).

### 4. Executar o pipeline

Abra o Jupyter no ambiente:

```bash
jupyter lab --no-browser
```

(ou selecione o kernel `mlops_lulc` diretamente no VS Code, sem servidor)

Notebook principal: [notebooks/sits_terraclass_mlflow.ipynb](notebooks/sits_terraclass_mlflow.ipynb)

Etapas do notebook:

| Seção | O que faz |
|-------|-----------|
| 0 | Config central (ROI, datas, MLflow tracking URI) |
| 1–3 | TerraClass → recorte da área de estudo → pontos de amostra por classe |
| 4 | Cria cubo Sentinel-2 do BDC via STAC (`sits_cube`) |
| 5 | Extrai séries temporais nos pontos (`sits_get_data`) |
| 6 | k-fold validation + treino Random Forest, com logging no MLflow |
| 7 | Classificação do cubo: probabilidades → suavização bayesiana → mapa temático |
| 8 | Mapa de incerteza (entropia) — base para Active Learning futuro |

⚠️ As seções 4, 5 e 7 carregam o R e processam rasters — execute uma por vez e monitore a memória.
A configuração padrão do notebook está reduzida (1 banda, 6 meses, 1 core) para caber em máquinas modestas; amplie após validar.

## Estrutura do repositório

```
├── docker-compose.yml      # MLflow standalone (SQLite)
├── environment.yml         # ambiente mamba: Python + R + sits + pysits
├── pyproject.toml          # metadados do pacote mlops_lulc
├── data/                   # dados de entrada (não versionados)
├── notebooks/              # pipeline exploratório
└── mlops_lulc/             # pacote Python (produção futura do pipeline)
    ├── dataloader/
    ├── preprocess/
    ├── train/
    ├── predict/
    ├── postprocess/
    └── utils/
```

## Roadmap

- [ ] Infra mínima: mamba (R+sits+pysits) + MLflow via Docker Compose
- [ ] Pipeline exploratório no notebook: amostras TerraClass → cubo BDC → treino → classificação
- [ ] Logging completo de métricas de validação (acurácia, kappa) no MLflow
- [ ] Ampliar período/bandas do cubo após validação em área pequena
- [ ] Refatorar células validadas para o pacote `mlops_lulc/`
- [ ] Testes do pacote
- [ ] (Opcional) Active Learning: amostragem por incerteza + retreino iterativo
- [ ] (Opcional) Orquestração com Airflow, se houver recursos



mamba activate mlops_lulc
mamba env update -n mlops_lulc -f environment.yml --prune
R -q -e 'torch::install_torch()'
R -q -e 'library(torch); print(torch_is_installed())'