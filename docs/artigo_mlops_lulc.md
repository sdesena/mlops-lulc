Sistematização do ciclo de vida de modelos de classificação de uso e cobertura da Terra baseada em práticas de MLOps 
Sandro de Sena Machado1, Jensen¹, Gilberto Ribeiro Queiroz¹, Karine Reis Ferreira¹
1Instituto Nacional de Pesquisas Espaciais (INPE)
## Sistematização do ciclo de vida de modelos de classificação de uso e cobertura da Terra baseada em práticas de MLOps

Sandro de Sena Machado¹, Jensen¹, Gilberto Ribeiro Queiroz¹, Karine Reis Ferreira¹  
¹ Instituto Nacional de Pesquisas Espaciais (INPE), São José dos Campos, SP, Brasil

## Resumo

Este trabalho apresenta um protótipo reprodutível para apoiar o ciclo de vida de modelos de classificação de uso e cobertura da Terra (LULC). O protótipo combina o pacote SITS, acessado por sua interface Python `pysits`, com imagens Sentinel-2 do Brazil Data Cube e o MLflow para rastreamento de experimentos. A avaliação é conduzida em uma área reduzida do Maranhão, utilizando polígonos do TerraClass 2024 como fonte de amostras. O objetivo não é propor um novo classificador, mas verificar como o registro sistemático de configurações, métricas, modelos e produtos cartográficos melhora a rastreabilidade e a reprodutibilidade de experimentos de sensoriamento remoto.

**Palavras-chave:** MLOps; LULC; séries temporais; SITS; MLflow; sensoriamento remoto.

## 1. Introdução

A classificação de uso e cobertura da Terra (LULC, do inglês *Land Use and Land Cover*) é importante para o monitoramento ambiental, a análise de mudanças e o planejamento territorial. Produtos como TerraClass e MapBiomas são atualizados periodicamente e dependem de etapas de preparação de dados, seleção de amostras, treinamento, avaliação e produção cartográfica.

Quando essas etapas são executadas manualmente e sem registro padronizado, torna-se difícil identificar quais dados, parâmetros e versões de código produziram determinado mapa. O problema é especialmente relevante em séries temporais, nas quais alterações de período, sensor, bandas e amostras podem modificar o resultado.

MLOps reúne práticas para organizar o ciclo de vida de aplicações de aprendizado de máquina, incluindo rastreamento de experimentos, versionamento, registro de artefatos e reprodutibilidade. Este trabalho explora essas práticas em um protótipo de classificação LULC baseado em séries temporais Sentinel-2.

O estudo utiliza uma arquitetura mínima, adequada a recursos computacionais limitados: um ambiente mamba para Python e R, um script executável pelo terminal, SITS para o processamento das séries e MLflow em um contêiner Docker independente. O JupyterLab permanece opcional, destinado à inspeção exploratória.

## 2. Fundamentação

### 2.1 Classificação de uso e cobertura da Terra

A classificação LULC atribui a uma unidade espacial, como um pixel, objeto ou trajetória temporal, uma categoria que descreve a cobertura física da superfície ou seu uso antrópico. Florestas, corpos d'água e vegetação natural são exemplos de cobertura; agricultura, pastagem e áreas urbanizadas são exemplos de uso.

O TerraClass disponibiliza classes temáticas em formatos vetorial e raster. Neste protótipo, os polígonos do TerraClass 2024 são recortados para a área de estudo e pontos são amostrados dentro das geometrias para formar os dados de treinamento.

### 2.2 Séries temporais de imagens de satélite

Uma série temporal representa a dinâmica sazonal e fenológica da superfície, em vez de utilizar somente uma imagem isolada. Essa informação pode ajudar a distinguir culturas agrícolas, pastagens e vegetação natural, que podem apresentar respostas semelhantes em uma data, mas trajetórias diferentes ao longo do tempo.

O pacote SITS (*Satellite Image Time Series*) oferece funções para construir cubos, extrair séries temporais, treinar classificadores, classificar cubos e aplicar pós-processamento. A interface `pysits` permite utilizar essas operações a partir do Python, mantendo o processamento principal em R. O Random Forest foi escolhido como baseline por ser simples, interpretável e suportado pelo SITS.

### 2.3 MLOps e ciclo de vida de modelos

Neste trabalho, MLOps é operacionalizado por quatro práticas: (i) rastreabilidade de ROI, período, bandas, amostras e parâmetros; (ii) reprodutibilidade do ambiente por `environment.yml`; (iii) comparação de execuções no MLflow; e (iv) associação de configurações, métricas, gráficos e mapas às respectivas runs.

O MLflow armazena os metadados das execuções em SQLite e os arquivos em um volume local. Essa configuração é suficiente para um experimento individual e pode ser substituída por serviços compartilhados em uma implantação futura.

## 3. Objetivos

### 3.1 Objetivo geral

Avaliar a utilidade de práticas de MLOps para tornar rastreável e reprodutível um workflow de classificação LULC baseado em séries temporais Sentinel-2.

### 3.2 Objetivos específicos

- Construir um ambiente reproduzível com Python, R, SITS e `pysits`.
- Extrair amostras do TerraClass 2024 em uma área reduzida do Maranhão.
- Criar um cubo Sentinel-2 do Brazil Data Cube e extrair séries temporais.
- Treinar e avaliar um Random Forest usando o SITS.
- Registrar parâmetros, resultados, métricas e produtos no MLflow.
- Comparar configurações simples de bandas e parâmetros do modelo.
- Reexecutar o baseline e verificar a equivalência das configurações e artefatos.

## 4. Metodologia

### 4.1 Área de estudo

A área está localizada no sul do Maranhão, na região de Balsas. Para manter o processamento compatível com uma máquina limitada, foi utilizado inicialmente um retângulo de aproximadamente 35 km por 35 km:

```text
longitude: -46.20 a -45.85
latitude:  -7.70 a -7.35
```

### 4.2 Dados e amostras

O arquivo vetorial do TerraClass 2024 está originalmente em EPSG:4674. Após o recorte, as geometrias são convertidas para EPSG:4326 e são gerados dez pontos aleatórios por classe, utilizando uma semente fixa. As amostras são exportadas em CSV e a área recortada é exportada em GeoJSON, formato simples de visualizar em ferramentas geoespaciais e de anexar como artefato.

Essa amostragem é exploratória. Como os pontos são derivados do próprio TerraClass, eles não constituem uma validação de campo independente.

### 4.3 Dados Sentinel-2 e atributos

As imagens são obtidas da coleção `SENTINEL-2-16D` do Brazil Data Cube por meio do catálogo STAC acessado pelo SITS. O baseline utiliza `NDVI` e um período de janeiro a março de 2024, resultando em seis datas temporais. Uma execução adicional pode incluir bandas como `B02`, `B03`, `B04`, `B08`, `B11` e `B12`.

### 4.4 Workflow computacional

O workflow é executado pelo script `scripts/run_pipeline.py`:

```text
TerraClass → recorte e amostras → cubo BDC → séries temporais
		  → validação k-fold → Random Forest → classificação opcional → MLflow
```

O script recebe ROI, datas, bandas, número de pontos e árvores por argumentos. A classificação raster é opcional porque é a etapa mais custosa. O processamento é limitado a um núcleo e, na classificação, a `memsize=1` para reduzir o risco de esgotamento de memória.

### 4.5 Infraestrutura

O `environment.yml` define Python, R, SITS, `pysits`, bibliotecas geoespaciais e MLflow. O MLflow é executado pelo Docker Compose em um único contêiner, com SQLite e volume local. O JupyterLab pode ser usado diretamente no ambiente mamba, mas não é necessário para executar o pipeline.

O GaiaFlow foi avaliado durante a configuração inicial, mas não faz parte da implementação final. Sua remoção reduziu dependências e pontos de falha, mantendo os componentes necessários para demonstrar SITS e MLOps.

## 5. Experimentos

### Experimento 1 — Baseline

Executar o workflow com NDVI, dez pontos por classe, janeiro a março de 2024 e Random Forest com 20 árvores. O resultado observado foi uma execução com 120 amostras, 12 classes, seis datas, `Accuracy = 0,2667` e `Kappa = 0,20`. Esses valores devem ser interpretados como baseline exploratório, não como desempenho final.

### Experimento 2 — Bandas adicionais

Repetir a execução com NDVI e bandas espectrais selecionadas, mantendo ROI, datas, semente e amostras constantes. A hipótese é que atributos adicionais melhorem a separação entre classes.

### Experimento 3 — Configuração do Random Forest

Comparar 20 e 100 árvores. O objetivo é demonstrar a comparação de runs e a recuperação dos parâmetros no MLflow, sem realizar uma busca exaustiva.

### Experimento 4 — Reprodutibilidade

Executar novamente o baseline com os mesmos argumentos e comparar configuração, distribuição das amostras, timeline, métricas e artefatos produzidos.

## 6. Métricas e artefatos

O resultado do `sits_kfold_validate` é salvo integralmente em `kfold_result.txt`. As métricas globais `Accuracy` e `Kappa` são extraídas automaticamente para `kfold_metrics.json` e registradas como métricas da run no MLflow. A matriz de confusão e as métricas por classe permanecem no resultado textual do SITS, permitindo inspeção posterior.

Cada execução produz ou registra `config.json`, `samples.csv`, `class_distribution.csv`, `study_area.geojson`, `samples_map.png`, `time_series.png`, `time_series_metadata.csv`, `kfold_result.txt`, `kfold_metrics.json` e `run_summary.json`. Quando habilitada, a classificação também registra os mapas de probabilidades e o mapa classificado.

## 7. Resultados esperados

Espera-se demonstrar que uma tarefa de classificação LULC pode ser organizada como uma sequência reproduzível de operações, mesmo sem uma plataforma distribuída. O resultado principal é a associação entre mapa, amostras, configuração, métricas, código e ambiente.

As evidências serão apresentadas por meio de uma tabela comparativa das runs no MLflow, gráfico de séries temporais, mapa da ROI e pontos de amostra, matriz de confusão, métricas por experimento e mapa classificado quando a infraestrutura suportar essa etapa.

## 8. Limitações e trabalhos futuros

O experimento utiliza uma área pequena, poucas amostras por classe e período temporal reduzido. A referência deriva do TerraClass e não representa validação de campo independente. Além disso, a avaliação atual usa amostras limitadas e deve ser ampliada antes de qualquer conclusão operacional.

Como trabalhos futuros, podem ser consideradas a divisão espacial entre treino e teste, a ampliação temporal, a inclusão de mais classes e bandas, a análise de incerteza, o registro formal do modelo, a execução anual e a orquestração com Airflow.

## Referências

KREUZBERGER, D.; KÜHL, N.; HIRSCHL, S. Machine Learning Operations (MLOps): Overview, Definition, and Architecture. *IEEE Access*, v. 11, p. 31866–31879, 2023. DOI: 10.1109/ACCESS.2023.3262138.

SANTOS, L.; FERREIRA, K.; CAMARA, G.; PICOLI, M.; SIMOES, R. Quality control and class noise reduction of satellite image time series. *ISPRS Journal of Photogrammetry and Remote Sensing*, v. 177, p. 75–88, 2021. DOI: 10.1016/j.isprsjprs.2021.04.014.

SIMOES, R.; CAMARA, G.; QUEIROZ, G.; et al. Satellite Image Time Series Analysis for Big Earth Observation Data. *Remote Sensing*, v. 13, n. 13, p. 2428, 2021. DOI: 10.3390/rs13132428.

SITS. *Satellite Image Time Series*. Disponível em: https://e-sensing.github.io/sitsbook/.

MLFLOW. *MLflow Documentation*. Disponível em: https://mlflow.org/docs/latest/.