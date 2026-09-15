**Sistematização do ciclo de vida de modelos de classificação de uso e cobertura da Terra**

*Sandro de Sena Machado¹, Maria Isabel Escada¹*

¹ Instituto Nacional de Pesquisas Espaciais (INPE)  
São José dos Campos, SP, Brasil

**Resumo**

Este trabalho apresenta um protótipo para sistematizar o ciclo de vida de modelos de classificação de uso e cobertura da Terra. O protótipo combina o pacote SITS, com cubos de dados Sentinel-2 do Brazil Data Cube e o MLflow para rastreamento de experimentos. A avaliação é conduzida em uma área ao redor do município de Balsas no Maranhão, utilizando polígonos do TerraClass 2024 como fonte de amostras. O objetivo não é propor um novo classificador, mas verificar como o registro sistemático de configurações, métricas, modelos e produtos cartográficos melhora a rastreabilidade e a reprodutibilidade de experimentos de sensoriamento remoto.

**1\. Introdução**

A classificação de uso e cobertura da Terra (LULC, do inglês *Land Use and Land Cover*) é essencial para o monitoramento ambiental, a análise de mudanças e o planejamento territorial. Mapeamentos como TerraClass \[1\] e MapBiomas \[2\], distintos em vários aspectos das respectivas metodologias \[3\], têm em comum o fato de serem atualizados periodicamente, com preparação de dados, seleção de amostras, treinamento, avaliação e produção cartográfica.  
Quando essas etapas são executadas manualmente e sem registro padronizado, torna-se difícil identificar quais dados, parâmetros e versões de código produziram determinado mapa. O problema é especialmente relevante em séries temporais, nas quais alterações de período, sensor, bandas e amostras podem mudar o resultado \[4\].  
Para lidar com tais problemas, o conceito de MLOps reúne práticas para sistematizar o ciclo de vida de aplicações de aprendizado de máquina, incluindo rastreamento de experimentos, versionamento, registro de artefatos, configurações, parâmetros, entre outros aspectos para garantir reprodutibilidade e rastreamento de mudanças ao longo do processo de desenvolvimento dos modelos \[5 , 6\].   
Este trabalho explora essas práticas em um protótipo de classificação LULC baseado em séries temporais Sentinel-2. Foi utilizada uma arquitetura básica, adequada a recursos computacionais limitados: um ambiente mamba para Python e R, o pacote SITS (*Satellite Imagery Time Series*) \[7\] para as rotinas de processamento e ajustes dos modelos, e MLflow \[8\] para rastreamento dos experimentos.

**2\. Fundamentação**  
**2.1 Classificação de uso e cobertura da Terra**

A classificação LULC atribui a uma unidade espacial, como um pixel, objeto ou trajetória temporal, uma categoria que descreve a cobertura física da superfície ou seu uso antrópico. Florestas, corpos d'água e vegetação natural são exemplos de cobertura; agricultura, pastagem e áreas urbanizadas são exemplos de uso \[9\].  
Parte do desafio do mapeamento está na própria definição de cada classe. As iniciativas de mapeamento de LULC como TerraClass e MapBiomas diferenciam-se desde a concepção do conceito de cada classe, até os métodos estatísticos de avaliação da qualidade. Ainda que seja possível utilizá-los de maneira complementar, o uso eficaz de cada um depende da aplicação \[3\].

**2.2 Séries temporais de imagens de satélite**

Uma série temporal em sensoriamento remoto representa a trajetória de mudança da imagem ao longo de um período. Essa informação pode ajudar a distinguir culturas agrícolas, pastagens e vegetação natural, que podem apresentar respostas semelhantes em uma data isolada, mas assinaturas espectrais diferentes ao longo do tempo \[7\].  
O pacote SITS oferece funções para construir cubos de dados multitemporais, extrair trajetórias, treinar classificadores, classificar cubos e aplicar pós-processamento \[7\]. 

**2.3 MLOps e ciclo de vida de modelos**

MLOps designa o conjunto de princípios, componentes e práticas que estendem a cultura DevOps ao desenvolvimento de sistemas de aprendizado de máquina, com o objetivo de automatizar e tornar rastreável o ciclo de vida dos modelos. O desenvolvimento de modelos organiza-se em torno da experimentação contínua com dados, algoritmos, bibliotecas e hiperparâmetros na busca por uma métrica-alvo, de modo que o desempenho passa a depender tanto do código quanto dos dados e do processo de treinamento \[10\].   
Em aplicações de sensoriamento remoto, tais desafios são acentuados pela periodicidade dos mapeamentos e pela sensibilidade dos resultados a escolhas de período, sensor, bandas e amostras, o que motivou trabalhos recentes a organizar a produção anual de mapas de cobertura da terra como um fluxo de MLOps \[4\].  
Entre as plataformas disponíveis para esse fim, o MLflow é uma solução de código aberto concebida sob uma filosofia de interfaces abertas \[10\]. Para fluxos geoespaciais, o registro de artefatos de natureza arbitrária é especialmente conveniente, pois o produto de uma execução não se resume a um valor de acurácia: amostras, gráficos de séries temporais e arquivos cartográficos permanecem vinculados à configuração que os originou.

**3\. Objetivos**  
**3.1 Objetivo geral**

Avaliar a utilidade de práticas de MLOps em termos de reprodutibilidade e experimentação científica num fluxo de trabalho de classificação LULC baseado em séries temporais de imagens de sensoriamento remoto.

**3.2 Objetivos específicos**

\- Construir um fluxo de trabalho de classificação de LULC a partir de cubos de dados.  
\- Executar experimentos e registrar parâmetros, resultados, métricas e produtos no MLflow.

**4\. Materiais e métodos**  
**4.1 Área de estudo**

A área está localizada no sul do Maranhão, na região de Balsas. Para manter o processamento compatível com uma máquina limitada, foi utilizado inicialmente um retângulo mínimo envolvente de aproximadamente 35 km por 35 km, descrito pelos pares de coordenadas (-46.20, \-7.70, \-45.85, \-7.35). A região de Balsas é um dos principais polos do agronegócio no estado, sendo o maior produtor de soja e com uma das maiores taxas de desmatamento do Maranhão.

**4.2 Amostragem**

As amostras de referência são derivadas do mapeamento TerraClass 2024, escolhido por ser a base oficial mais recente para os biomas Amazônia e Cerrado. Esse mapeamento indica que cerca de 64% do território dos dois biomas mantém vegetação natural primária preservada, enquanto 18% corresponde a pastagens e 7% à agricultura, incluindo cultivos temporários, semiperenes, perenes e silvicultura \[11\].   
A área de estudo, situada no Cerrado maranhense, insere-se na porção agrícola dessa dinâmica: as culturas temporárias representam 19% das áreas antropizadas dos dois biomas, com predomínio da agricultura de mais de um ciclo anual (68% das áreas de produção), e a agricultura anual expandiu-se 10% entre 2022 e 2024, majoritariamente sobre usos agropecuários já consolidados. Esse contexto é relevante para o experimento porque implica classes espectralmente próximas e fortemente dependentes do calendário agrícola, condição em que a discriminação por séries temporais é mais informativa do que a classificação por data isolada.  
O arquivo vetorial do TerraClass 2024 está originalmente em EPSG:4674. O preprocessamento consiste em recortar as geometrias pelo retângulo envolvente definido na Seção 4.1, reprojetá-las para EPSG:4326 e sortear pontos aleatórios no interior de cada polígono, com semente fixa, de modo que a mesma configuração produza sempre o mesmo conjunto de amostras. O número de pontos por polígono é um parâmetro da execução, o que permite tratar o tamanho da amostra como variável experimental e observar seu efeito sobre as métricas.  
Cabe ressaltar que, por serem derivados do próprio TerraClass, os pontos herdam suas eventuais imprecisões e não constituem validação de campo independente.

**4.3 Imagens de satélite**

As imagens foram obtidas da coleção SENTINEL-2-16D do Brazil Data Cube por meio do catálogo STAC acessado via SITS. Foram avaliadas configurações com o índice NDVI e com bandas espectrais Sentinel-2. A configuração mais abrangente utilizou B02, B03, B04, B08, B11, B12 e NDVI, entre 1º de janeiro e 30 de junho de 2024. Esse intervalo produziu doze datas na timeline do cubo, com composição nominal de dezesseis dias.

**4.4 Fluxo de trabalho**

Neste trabalho, a sistematização do ciclo de vida dos modelos é operacionalizada por quatro práticas: (i) rastreabilidade da área de treinamento, período, bandas, amostras e parâmetros; (ii) associação de configurações, métricas, gráficos e mapas às respectivas runs; (iii) comparação de execuções e experimentos no MLflow; (iv) reprodutibilidade do ambiente através de manifestos e contêineres.  
A interface pysits permite utilizar essas operações a partir do Python, mantendo o processamento principal em R. O algoritmo Random Forest foi escolhido como baseline por ser simples, interpretável e suportado pelo SITS.  
O MLflow armazena os metadados das execuções em banco SQLite e os arquivos em um volume local. O script registra a configuração da run, o commit do código, versões do Python e do pysits, tempos por etapa, métricas de validação e artefatos intermediários. Entre os artefatos estão a distribuição das classes, os pontos amostrados, o mapa das amostras, o gráfico das séries temporais e o resultado textual da matriz de confusão. A classificação do cubo é uma etapa opcional, seguida, no SITS, pela suavização e pela rotulação da classificação.

O processamento foi executado localmente em WSL2. Nas primeiras execuções, o paralelismo foi mantido baixo devido ao consumo de memória; posteriormente, foram testados valores maiores de `multicores` nas etapas de construção do cubo, extração e validação. A alteração do paralelismo foi tratada como decisão operacional de desempenho, e não como variável de comparação da qualidade do modelo.

**5\. Resultados**

Foram realizadas execuções exploratórias no experimento `sits-terraclass-balsas-v2`. As principais configurações e resultados, recuperados dos artefatos locais e do MLflow, são apresentados de forma compacta a seguir:

- **`baseline-6classes`**: janeiro a março de 2024, NDVI, dez pontos por classe, seis classes e 20 árvores; Accuracy de 0,3833, Kappa de 0,2600 e tempo total de aproximadamente 21,5 minutos.
- **`baseline-v2`**: janeiro a março de 2024, NDVI, dez pontos por classe, doze classes e 20 árvores; Accuracy de 0,2667, Kappa de 0,2000 e tempo total de aproximadamente 22,9 minutos.
- **`multibanda-6classes`**: janeiro a março de 2024, B02, B03, B04, B08 e NDVI, 20 pontos por classe, seis classes e 30 árvores; Accuracy de 0,3833, Kappa de 0,2600 e tempo total de aproximadamente 97,6 minutos.
- **`6meses-multibanda-6classes-classify`**: janeiro a junho de 2024, B02, B03, B04, B08, B11, B12 e NDVI, 30 pontos por classe, seis classes e 50 árvores; Accuracy de **0,6222**, Kappa de **0,5467** e aproximadamente 4,07 horas até o treinamento.

As runs de três meses mostram dois efeitos distintos: `baseline-v2` preservou a configuração NDVI e utilizou as doze classes disponíveis, enquanto `multibanda-6classes` restringiu o problema a seis classes e adicionou bandas espectrais. A run `baseline-6classes` também utilizou seis classes, mas com NDVI e dez pontos por classe. Essas diferenças tornam a comparação útil para documentar a evolução do protótipo, mas insuficiente para separar causalmente os efeitos de classes, bandas e tamanho da amostra.

A melhor execução utilizou 180 amostras, doze datas temporais e seis classes. A acurácia foi de 62,22%, com intervalo de confiança de 95% entre 54,71% e 69,33%, e Kappa de 0,5467. Em relação a `baseline-6classes`, houve aumento de 23,89 pontos percentuais na acurácia e de 0,2867 no Kappa. O resultado indica uma melhora observada na configuração mais abrangente, mas não permite atribuir o ganho a uma única modificação.

As métricas por classe da melhor execução foram:

| Classe | Recall | Precisão | F1 |
|---|---:|---:|---:|
| Vegetação natural primária | 0,4000 | 0,4138 | 0,4068 |
| Vegetação natural secundária | 0,5667 | 0,5484 | 0,5574 |
| Cultura agrícola temporária de mais de um ciclo | 0,7667 | 0,7419 | 0,7541 |
| Corpo d'água | 0,7667 | 0,9200 | 0,8364 |
| Cultura agrícola temporária de um ciclo | 0,6333 | 0,6129 | 0,6230 |
| Pastagem | 0,6000 | 0,5455 | 0,5714 |

O melhor desempenho ocorreu para corpo d'água e cultura agrícola temporária de mais de um ciclo. As maiores dificuldades ocorreram em vegetação natural primária, vegetação natural secundária e pastagem. A matriz de confusão mostra que essas classes são frequentemente confundidas entre si, enquanto as duas classes agrícolas também apresentam confusão mútua. O F1 médio das seis classes foi aproximadamente 0,625, próximo da acurácia global, sem evidência de que o resultado global tenha sido produzido apenas por uma classe dominante.

O registro dos tempos de execução permitiu identificar o principal gargalo da melhor run. A preparação consumiu 43 segundos, a construção do cubo 16,8 minutos, a extração das séries 3,78 horas, a validação 2,3 segundos e o treinamento final menos de um segundo. Assim, aproximadamente 93% do tempo medido até o treinamento foi consumido pela extração das séries temporais, e não pelo ajuste do Random Forest. A classificação do cubo foi iniciada em uma execução específica, mas não foi considerada no tempo acima, pois essa etapa permaneceu incompleta em razão do custo computacional e de problemas de acesso a dados remotos.

Além das métricas, as runs produziram configurações, CSVs de amostras, geometrias da área de estudo, mapas das amostras, gráficos de séries temporais, matriz de confusão e resumos de execução. Esse conjunto permite reconstruir a relação entre entrada, parâmetros, avaliação e produto, que não estaria disponível apenas com o valor de acurácia.

**6\. Discussão**

Os resultados mostram uma diferença expressiva entre a configuração inicial de seis classes e a configuração de seis meses, com mais atributos, mais amostras e mais árvores. A acurácia passou de 0,3833 para 0,6222 e o Kappa de 0,2600 para 0,5467. Esse resultado é compatível com a hipótese de que informação temporal e espectral adicional pode ajudar a separar classes de uso e cobertura da terra. Entretanto, essa interpretação deve ser apresentada como hipótese apoiada por uma comparação exploratória, e não como efeito causal isolado.

O desenho realizado não separou adequadamente um grupo controle e grupos experimentais. Na melhor run foram alterados simultaneamente o período, o número de datas, as bandas, o número de pontos por classe e o número de árvores. Portanto, não é possível determinar quanto do ganho veio da janela temporal, das bandas SWIR, do tamanho da amostra ou do hiperparâmetro do Random Forest. A comparação entre as runs deve ser entendida como uma evolução de configurações, não como um experimento fatorial ou uma análise de ablação.

Essa é uma limitação central em relação à sistematização científica do ciclo de vida dos modelos. O pipeline registrou as execuções, mas o protocolo experimental ainda não definiu previamente uma pergunta para cada fator, uma condição controle, uma variável independente por vez, repetições suficientes e um critério de seleção independente. O MLflow garantiu rastreabilidade do que foi executado, mas rastreabilidade não equivale, por si só, a um desenho experimental rigoroso. Essa distinção é importante: o trabalho demonstra uma base operacional para MLOps, mas ainda não uma sistematização completa do processo de investigação e desenvolvimento do modelo.

O desempenho por classe também limita a interpretação da acurácia global. Corpo d'água apresentou F1 de 0,8364 e precisão de 0,9200, enquanto vegetação natural primária apresentou F1 de 0,4068. Isso sugere que a matriz de confusão e as métricas por classe são mais informativas do que a acurácia isolada. As confusões entre vegetação natural e pastagem podem estar associadas à proximidade espectral, à heterogeneidade dos polígonos ou à própria incerteza da referência TerraClass.

Do ponto de vista computacional, o treinamento foi barato quando comparado à extração das séries. O gargalo foi a leitura de dados remotos do BDC, que também introduziu falhas de disponibilidade de assets durante algumas execuções. A classificação do cubo completo é ainda mais custosa por operar sobre todos os pixels da área de interesse. Esses fatos reforçam que o ciclo de vida precisa registrar não apenas métricas preditivas, mas também tempo por etapa, status da execução, erros, dependências externas e artefatos parciais.

Como melhoria metodológica, o próximo protocolo deve fixar uma configuração controle e variar um único fator por vez. Por exemplo, mantendo classes, amostras, árvores e período constantes, podem ser comparados NDVI contra multibanda; em seguida, mantendo as bandas fixas, podem ser comparados três e seis meses; por fim, o tamanho da amostra e o número de árvores podem ser avaliados em experimentos separados. Cada configuração deve ser repetida com sementes controladas, e a comparação deve usar métricas globais, métricas por classe, intervalos de confiança e custo computacional.

Também é necessário substituir ou complementar o k-fold aleatório por uma validação espacial. Como os pontos são derivados de polígonos próximos e da mesma base temática, amostras espacialmente correlacionadas podem aparecer em treinamento e validação. Uma divisão por blocos ou por polígonos, com uma área de teste mantida fora do treinamento, forneceria uma estimativa mais realista da capacidade de generalização.

Nesse protocolo ampliado, o MLflow deve funcionar como registro de um ciclo de vida planejado: hipótese e plano da run, versão dos dados e do código, execução, avaliação, comparação com o controle, aprovação ou rejeição do modelo e registro do produto cartográfico. Essa evolução aproxima o protótipo de uma sistematização efetiva, em vez de limitar a plataforma ao armazenamento posterior de resultados.

**7\. Conclusões**

O protótipo mostrou ser viável para integrar SITS, cubos Sentinel-2 do Brazil Data Cube e MLflow em um ambiente local. Foi possível executar a preparação de amostras, a construção do cubo, a extração de séries temporais, a validação do Random Forest e o registro de parâmetros, métricas, tempos e artefatos cartográficos. A combinação desses componentes tornou as execuções mais comparáveis e facilitou a identificação de gargalos e falhas de dependências externas.

A configuração mais abrangente apresentou os melhores resultados observados, com Accuracy de 0,6222 e Kappa de 0,5467, contra 0,3833 e 0,2600 na configuração de seis classes e período mais curto. As métricas por classe mostraram melhor desempenho para corpo d'água e cultura agrícola de mais de um ciclo, e maior dificuldade para vegetação natural primária. Esses resultados são relevantes como evidência exploratória de que a configuração temporal e espectral influencia a classificação, mas não permitem concluir qual fator foi responsável pelo ganho.

A principal conclusão metodológica é que o trabalho alcançou uma primeira camada de sistematização operacional, mas não completou a sistematização científica do ciclo de vida dos modelos. O MLflow registrou o que foi executado; a etapa seguinte deve definir previamente como os experimentos serão planejados, controlados, repetidos, avaliados e promovidos. Sem grupo controle, isolamento das variáveis e validação espacial independente, os resultados não devem ser apresentados como uma demonstração causal da superioridade de uma configuração.

Como continuidade, recomenda-se: (i) estabelecer um protocolo de ablação com controle e uma variável alterada por vez; (ii) repetir as configurações e reportar incerteza; (iii) adotar validação espacial e, quando possível, referência independente do TerraClass; (iv) registrar estados de execução, falhas e retomada de etapas; (v) incorporar mapas de incerteza e análise da matriz de confusão; e (vi) comparar classificadores dentro do mesmo protocolo. Essas extensões fariam o MLflow apoiar não apenas a rastreabilidade dos experimentos, mas o ciclo completo de decisão sobre os modelos.

**Referências**

\[1\] ALMEIDA, C.A.; Coutinho, A.C.; Esquerdo, J.C.D.M.; Adami, M.; Venturieri, A.; Diniz, C.G.; Dessay, N.; Durieux, L.; Gomes, A.R. 2016\. **High spatial resolution land use and land cover mapping of the Brazilian Legal Amazon in 2008 using Landsat-5/TM and MODIS data**. Acta Amazonica, 46: 291-302.

\[2\] SOUZA Jr, C. M., Shimbo, J. Z., Rosa, M. R., Parente, L. L., Alencar, A. A., Rudorff, B. F., ... & Azevedo, T. (2020). **Reconstructing Three Decades of Land Use and Land Cover Changes in Brazilian Biomes with Landsat Archive and Earth Engine**. Remote Sensing, 12(17), 2735\. DOI: 10.3390/rs12172735.

\[3\] NEVES, A.K.; Körting, T.S.; Fonseca, L.M.G.; Escada, M.I.S. 2020\. **Assessment of TerraClass and MapBiomas data on legend and map agreement for the Brazilian Amazon biome**. Acta Amazonica.

\[4\] BURGUEÑO-ROMERO, Antonio M.; BARBA-GONZÁLEZ, Cristóbal; ALDANA-MONTES, José F. **Big Data-driven MLOps workflow for annual high-resolution land cover classification models**. Future Generation Computer Systems, v. 163, p. 107499, 2025\.

\[5\] BERBERI, **Lisana et al. Machine learning operations landscape: platforms and tools.** Artificial Intelligence Review, v. 58, n. 6, p. 167, 2025\.

\[6\] KREUZBERGER, D.; KÜHL, N.; HIRSCHL, S. **Machine Learning Operations (MLOps): Overview, Definition, and Architecture.** IEEE Access, v. 11, p. 31866–31879, 2023\. DOI: 10.1109/ACCESS.2023.3262138.

\[7\] SIMOES, R.; CAMARA, G.; QUEIROZ, G.; et al. **Satellite Image Time Series Analysis for Big Earth Observation Data.** Remote Sensing, v. 13, n. 13, p. 2428, 2021\. DOI: 10.3390/rs13132428.

\[8\] MLFLOW. **MLflow** Documentation. Disponível em: [https://mlflow.org/docs/latest/](https://mlflow.org/docs/latest/).

\[9\] TURNER B. L. II & W. B. Meyer, Global Land Use and Land Cover Change: An Overview , in Changes in land use and land cover: a global perspective, editado por W. Meyer e B. L. Turner II (Cambridge University Press, 1994), 3–10.

\[10\] ZAHARIA, Matei et al. Accelerating the machine learning lifecycle with MLflow. **IEEE Data Eng. Bull.**, v. 41, n. 4, p. 39-45, 2018\. 

\[11\] BRASIL. Instituto Nacional de Pesquisas Espaciais. TerraClass divulga dados atualizados sobre cobertura e uso da terra no bioma Amazônia. Disponível em: \<[https://www.gov.br/inpe/pt-br/assuntos/ultimas-noticias/terraclass-divulga-dados-atualizados-sobre-cobertura-e-uso-da-terra-no-bioma-amazonia](https://www.gov.br/inpe/pt-br/assuntos/ultimas-noticias/terraclass-divulga-dados-atualizados-sobre-cobertura-e-uso-da-terra-no-bioma-amazonia)\> Acesso em 14 de set.