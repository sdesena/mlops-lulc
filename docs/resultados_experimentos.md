# Resumo dos Experimentos — SITS + MLflow (LULC Balsas-MA)

Experimento MLflow: `sits-terraclass-balsas-v2`
Fonte: Sentinel-2 (BDC), ROI: Balsas-MA (-46.20, -7.70, -45.85, -7.35)

## Comparativo das runs

| Run | Bandas | Período | Amostras/classe | Classes | Árvores RF | Accuracy | Kappa | Tempo total | Classificação |
|---|---|---|---|---|---|---|---|---|---|
| `baseline` | NDVI | 2024-01 a 03 | 10 | 12 (todas) | 20 | 0.23 | 0.11 | ~12,1 min | Não |
| `baseline-6classes` | NDVI | 2024-01 a 03 | 10 | 6 | 20 | 0.38 | 0.26 | ~21,5 min | Não |
| `multibanda-6classes` | NDVI, B02, B03, B04, B08 | 2024-01 a 03 | 20 | 6 | 30 | 0.38 | 0.26 | ~97,6 min | Não |
| **`6meses-multibanda-6classes-classify`** | B02, B03, B04, B08, NDVI, B11, B12 | 2024-01 a 06 | 30 | 6 | 50 | **0.62** | **0.54** | ~4h04min (até o treino; classificação ainda em andamento) | **Sim** (em execução) |

> Nota: `baseline` não possui `kfold_metrics.json`/`run_summary.json` — parece ter sido interrompida antes de concluir a validação.
> Nota: `baseline-v2` e `multibanda-6classes` têm exatamente a mesma configuração e métricas — possivelmente a mesma run duplicada/reexecutada.

## Destaque: melhor resultado até agora

**`6meses-multibanda-6classes-classify`**
- **Accuracy: 62,22%** — quase o dobro das runs anteriores (~38%)
- **Kappa: 0,5467** — concordância "moderada a substancial", ante ~0,26 (fraca) nas runs anteriores
- Ganho atribuído a: série temporal mais longa (6 meses / 12 datas vs. 3 meses / 6 datas), mais bandas espectrais (incluindo SWIR B11/B12), mais amostras por classe (30 vs. 10-20) e mais árvores no Random Forest (50 vs. 20-30)

### Classes utilizadas (6 classes, consistente em todas as runs filtradas)
- Cultura Agrícola Temporária de 1 Ciclo
- Cultura Agrícola Temporária de Mais de 1 Ciclo
- Pastagem
- Vegetação Natural Primária
- Vegetação Natural Secundária
- Corpo D'água

## Tempo de execução por etapa (`6meses-multibanda-6classes-classify`)

| Etapa | Tempo |
|---|---|
| Preparação (amostragem) | 43 s |
| Construção do cubo (download BDC) | 16,8 min |
| Extração das séries temporais | **3h46min** (gargalo principal) |
| Validação k-fold | 2,3 s |
| Treinamento final | 0,08 s |
| **Classificação do cubo completo** | em andamento (não incluído no `elapsed_seconds` acima) |

## Artefatos disponíveis para a apresentação

- `samples_map.png` — mapa de amostras sobre a ROI (todas as runs)
- `time_series.png` — perfis NDVI das séries temporais amostradas (runs com métricas completas)
- `kfold_result.txt` — matriz de confusão completa (todas as runs com validação)
- `class_distribution.csv` — contagem de polígonos por classe
- Mapa classificado (`classified/*.tif`) — **ainda não gerado**, pendente da run em execução

## Pendências
- Aguardar conclusão do `sits_classify` → `sits_smooth` → `sits_label_classification` na run `6meses-multibanda-6classes-classify` para obter o mapa classificado final.
- Investigar por que `baseline-v2` e `multibanda-6classes` têm configuração/métricas idênticas.