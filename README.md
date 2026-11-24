# GeoExplora IA

> Plataforma de apoio à exploração de terras raras e minerais críticos em Angola. **TerraVisão** é o seu módulo de detecção remota. Ver [docs/14-geoexplora-ia.md](docs/14-geoexplora-ia.md).

## TerraVisão — módulo de prospecção por satélite

Ferramenta de **triagem** que analisa um terreno em Angola com dados públicos de satélite e indica a probabilidade (Alta / Média / Baixa) de ferro, cobre, ouro e água subterrânea, para orientar onde vale a pena ir ao campo.

> Estado: especificação concluída e esqueleto do código pronto (validação de terreno, índices, pontuação). Progresso em [CHECKLIST.md](CHECKLIST.md). Para contribuir, ver [CONTRIBUTING.md](CONTRIBUTING.md).

## Documentação

Comece por [docs/README.md](docs/README.md), que tem o índice e a ordem de leitura recomendada.

| Doc | Conteúdo |
|---|---|
| [01 Visão do produto](docs/01-visao-produto.md) | Problema, público, âmbito, o que o MVP não faz |
| [02 Requisitos](docs/02-requisitos.md) | Histórias de utilizador, requisitos funcionais e não funcionais, critérios de aceitação |
| [03 Arquitectura](docs/03-arquitectura.md) | Componentes, fluxo, estrutura de pastas, stack |
| [04 Dados e fontes](docs/04-dados-e-fontes.md) | Fontes públicas, bandas, resolução, licenças, cache |
| [05 Pipeline de análise](docs/05-pipeline-analise.md) | Índices espectrais, topografia, pontuação, classificação, zonas |
| [06 Interface (UX)](docs/06-interface-ux.md) | Ecrãs, fluxo, mapas, relatório |
| [07 Modelo de dados e contratos](docs/07-modelo-dados-contratos.md) | Esquemas de entrada/saída, interfaces dos módulos |
| [08 Plano e backlog](docs/08-plano-backlog.md) | Fases, tarefas, definição de pronto, roadmap pós-MVP |
| [09 Riscos e limitações](docs/09-riscos-limitacoes.md) | Riscos técnicos, científicos e de produto |
| [10 Decisões e questões abertas](docs/10-decisoes-questoes-abertas.md) | ADRs e perguntas a resolver |
| [11 Glossário](docs/11-glossario.md) | Termos técnicos e geológicos |
| [12 Design e interface](docs/12-design-ui.md) | Direcção visual, paleta, tipografia, layout |
| [16 Interface React](docs/16-interface-react.md) | Fluxo, dois sistemas, design system azul, API |
| [15 Roteiro de demonstração](docs/15-roteiro-demonstracao.md) | Sequência e respostas para a apresentação da SAGEO |
| [14 GeoExplora IA: visão e âmbito](docs/14-geoexplora-ia.md) | Produto, módulos, registo do que entra e do que fica de fora e porquê |
| [13 Guia Docker](docs/13-guia-docker.md) | Como executar noutro computador, teste offline e validação |
| [Anexo: protótipo GeoExplora IA](docs/anexos/prototipo-geoexplora-ia.md) | Resumo do PDF anterior (Longonjo) |

## Arranque rápido

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
terravisao check-aoi caminho\para\terreno.geojson
```

## Ver a interface

A interface é React + shadcn/ui (pasta `frontend/`), servida pela API FastAPI (docs/16).

```powershell
pip install -e ".[geo,analysis,report,web]"
cd frontend; npm ci; npm run build; cd ..
python -m geoexplora.web --port 8501
```

Abra http://localhost:8501. Em desenvolvimento: `python -m geoexplora.web --port 8000` e, noutra janela, `npm run dev` em `frontend/` (o Vite encaminha `/api` para a porta 8000).

Plano B (interface antiga em Streamlit): `pip install -e ".[geo,analysis,app,report]"` e `streamlit run app/streamlit_app.py`.

Pela linha de comandos:

```powershell
terravisao run data/samples/longonjo.geojson --out output/longonjo
terravisao report output/longonjo
```

## Estrutura

```
src/terravisao/   núcleo científico (funções puras, testável)
app/              interface Streamlit (só orquestra)
tests/            testes automáticos
data/reference/   dados de referência versionados
docs/             documentação do produto e da implementação
```
