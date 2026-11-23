# 10 — Decisões e questões abertas

## 1. Decisões tomadas (ADR resumidos)

| ID | Decisão | Razão | Alternativa rejeitada |
|---|---|---|---|
| ADR-01 | Método = sobreposição multicritério ponderada | Sem dados rotulados; explicável; calibrável por geofísico | ML supervisionado (sem rótulos) |
| ADR-02 | Interface em Streamlit | Rápido, Python puro, já usado no protótipo anterior | React + API (mais custo no MVP) |
| ADR-03 | Pacote `terravisao` separado da UI | Testável, reutilizável no Colab | Lógica dentro do Streamlit |
| ADR-04 | Grelha comum de 20 m | Compatível com SWIR do Sentinel-2, mais leve que 10 m | 10 m (mais pesado) |
| ADR-05 | Fuso UTM automático por AOI | Angola cobre 32S–34S | Fixar 33S (erro em áreas fora do fuso) |
| ADR-06 | Área máxima 2 500 km² | Limites de memória/tempo gratuitos | Sem limite |
| ADR-07 | Falhas parciais não bloqueiam a análise | Robustez (RNF-08) | Abortar em qualquer falha |
| ADR-08 | Resultado = probabilidade + confiança separadas | Honestidade científica | Só uma classe |
| ADR-09 | Só fontes gratuitas e abertas | Custo zero | APIs comerciais |
| ADR-11 | Interface 2D em Streamlit com **vista 3D opcional via pydeck**. Sem Three.js no MVP | Resultados são mapas 2D; pydeck é nativo no Streamlit e trata de geo-coordenadas | Three.js (sem suporte geoespacial, exige componente próprio); frontend 3D completo com CesiumJS/React (fase 2, se justificado) |
| ADR-12 | Distribuição do MVP para apresentação: **Docker local**. Quem quiser corre `docker compose up` a partir do repositório (que será público) e abre `localhost:8501`. A imagem inclui dados de demonstração pré-calculados (Longonjo, Huíla) para funcionar sem internet; a análise ao vivo é opcional | Custo zero, igual em qualquer computador, sem depender de servidor externo numa demonstração | Hospedagem online (Hugging Face Spaces, mesmo Dockerfile, fica como extra futuro); Streamlit em Cloudflare Workers (sem suporte a GDAL) |
| ADR-13 | DEM = Copernicus GLO-30 (Earth Search/AWS) em vez de SRTM directo | Mesma resolução (~30 m), acesso aberto sem credenciais via STAC, mesmo cliente do Sentinel-2. SRTM fica como alternativa | SRTM via USGS (exige conta) |
| ADR-14 | Papel da IA no MVP: **assistente de chat opcional, nunca um pilar**. Interpreta os resultados (responde, filtra zonas, escreve o relatório); lê só o resultado por funções fixas e não faz cálculos nem previsões. Todas as funções do sistema funcionam sem ele | Utilidade real sem inventar ciência; o produto não pode depender de um serviço externo | IA a prever minério sem dados rotulados; LLM com acesso livre aos dados |
| ADR-15 | Fornecedor do assistente: **Cloudflare Workers AI**, com o token da conta (gratuita) de cada utilizador. Sem Claude nem Ollama: os computadores disponíveis são fracos para modelos locais | Plano gratuito (10 000 neurons/dia), sem custo para o projecto; cada utilizador gasta a sua quota e o token nunca vai para o repositório | Claude API (custo e chave); Ollama local (hardware fraco); token partilhado do dono (quota e risco) |
| ADR-16 | Geologia não é bloqueante: o MVP segue sem mapa geológico e com confiança limitada a "média". O shapefile do BGS (1:5M) fica como melhoria opcional quando a licença for confirmada | Evita depender de licença por confirmar; a regra de confiança já cobre a ausência | Esperar pela geologia antes de avançar |
| ADR-10 | Nome oficial do produto: **TerraVisão**. "GeoExplora IA" fica como nome do protótipo anterior (Q-06 resolvida) | Decisão do dono do projecto | Manter dois nomes |

## 2. Questões abertas

| ID | Questão | Quem decide | Bloqueia |
|---|---|---|---|
| Q-01 | O OneGeology tem cobertura vectorial de Angola com litologia utilizável? Que escala e licença? | Spike T-001 | Camada de litologia |
| Q-02 | Qual fonte de Sentinel-2 usar: Copernicus Data Space, Planetary Computer ou AWS? | Spike T-002 | Módulo `ingest` |
| Q-03 | Pesos e limiares iniciais estão adequados? | Geofísico (o dono do projecto) | Fase 3 |
| Q-04 | Quais litologias de Angola são favoráveis a ferro, cobre, ouro, água? | Geofísico | Tabela de litologia |
| Q-05 | folium Draw ou leafmap para desenhar polígonos no Streamlit? | Spike T-005 | UI |
| Q-15 | Deteção de anomalias não supervisionada (PCA/Isolation Forest) entra no MVP como camada opcional ou fica para a fase 2? | Dono do projecto | Posicionamento "IA" |
| Q-16 | Que modelo do Workers AI no plano gratuito responde bem em português e segue instruções estritas (citar valores, recusar certezas)? | Spike no T-213 | T-213, T-216 |
| Q-13 | O pydeck aguenta o relevo 3D com a camada de textura em AOIs grandes? Se não, reduzir resolução ou limitar a vista 3D a AOIs menores | Spike T-007 | RF-24 |
| Q-08 | Quais são as áreas de teste e onde há verdade de campo (além de Longonjo)? | Geofísico | Validação |
| Q-09 | Haverá acesso a dados nacionais (levantamentos aeromagnéticos do Instituto Geológico) para a fase 2? | Dono do projecto | Roadmap |
| Q-10 | Termos de uso e responsabilidade legal do relatório | Dono do projecto / jurídico | Lançamento |
| Q-12 | O relatório PDF deve ter marca/logótipo? | Dono do projecto | T-207 |

## 3. Como registar novas decisões

Adicionar linha em §1 com ID sequencial `ADR-nn`, razão e alternativa rejeitada; mover a questão correspondente de §2 e anotar a resposta.
