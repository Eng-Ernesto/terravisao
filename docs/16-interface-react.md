# 16 — Interface (React + shadcn/ui): fluxo, sistemas e design

Substitui a interface Streamlit como interface principal. O Streamlit fica no repositório como plano B até a nova estar verificada.

## 1. Decisões (24 de Novembro)

| Tema | Decisão |
|---|---|
| Tecnologia | React + TypeScript (Vite), Tailwind e **shadcn/ui**; animações com Motion |
| Backend | API FastAPI por cima dos pacotes `geoexplora` e `terravisao` (nada da ciência muda) |
| Estrutura | **Dois sistemas separados**: Análise de mapa e TerraVisão. Cada um tem o seu menu; troca-se de sistema pelo menu |
| Tema | **Claro e azul** (referência: Google Drive). Óxido, ocre e musgo só nas classes de anomalia |
| Guia inicial | Aparece na **primeira entrada** em cada sistema; botão **Saltar**; fechado ou saltado não volta a aparecer; pode ser revisto no menu («Guia») |
| Offline | Componentes, fontes e mapa (Leaflet) empacotados; nenhum CDN |

## 2. Fluxo

```
Abertura (animada) ─ Iniciar ─▶ Escolha do sistema ─┬─▶ Análise de mapa (menu próprio)
                                                    └─▶ TerraVisão      (menu próprio)
          (primeira entrada em cada sistema: guia de 3 passos, com Saltar)
```

### Abertura
Fundo claro com gradiente azul suave. Em sequência (esvanecer): nome **GeoExplora IA** → frase «Interprete dados de minerais críticos em minutos» → três ideias (Os seus dados · Análise explicável · Relatório técnico) → botão **Iniciar**. **Saltar** sempre visível.

### Escolha do sistema
Dois cartões grandes, lado a lado: **Análise de mapa** («Carregue os seus dados; a IA analisa») e **TerraVisão** («Desenhe um terreno; análise por satélite»). Cada cartão tem o botão de entrada.

### Sistema Análise de mapa (chat primeiro)
Menu lateral: **Nova análise** · **Mapa** · **Relatório** · **Guia** · **Definições da IA** · *Ir para o TerraVisão* · *Início*.

- **Nova análise:** saudação, zona para largar ficheiros (CSV, GeoJSON, Shapefile .zip, GeoTIFF) e atalhos «Exemplo da equipa» e «Modelo coerente». Depois de carregar: conversa com a IA. A primeira resposta traz **cartões** (classificação, zonas, relação com a geofísica, modelo). Sugestões em pílulas e caixa de pergunta em baixo.
- **Mapa:** amostras por classe, zonas, superfície e grelhas geofísicas (com derivadas), sobre a imagem de satélite do TerraVisão quando existe. Não é obrigatório: a análise faz-se no chat.
- **Relatório:** descarregar o PDF técnico e as amostras classificadas (CSV).
- **Definições da IA:** Account ID e token da Cloudflare (guardados só na sessão do navegador). Sem eles, o assistente responde offline.

### Sistema TerraVisão (mapa primeiro)
Menu lateral: **Nova análise** · **Resultados** · **Guia** · *Ir para a Análise de mapa* · *Início*.

- **Nova análise:** mapa grande; desenhar rectângulo ou polígono, ou carregar GeoJSON; validação imediata (área, dentro de Angola); escolher alvos; **Analisar** com barra de progresso; ao terminar abre o resultado.
- **Resultados:** lista de terrenos (exemplos e análises feitas); mapa com camadas (classe, pontuação, óxido de ferro, argila, relevo, satélite) e zonas; resumo e tabela de zonas; exportar PDF e dados.

## 3. Design system

| Token | Valor | Uso |
|---|---|---|
| `--primary` | azul `#1A5BD7` | Acções, menu activo, ligações |
| `--primary-soft` | `#E8F0FE` | Fundos de destaque, item activo do menu |
| `--background` | `#F5F7FB` | Fundo da app |
| `--card` | `#FFFFFF` | Cartões, painéis (cantos 16 px, sombra suave) |
| `--foreground` | `#0F1B2D` | Texto |
| `--muted-foreground` | `#5B6B82` | Texto secundário |
| `--border` | `#E2E8F2` | Bordas |
| Classe baixa / moderada / elevada | `#5E7A63` / `#C9A227` / `#B4532A` | Só nas classes de anomalia (mesmas cores do PDF) |

- Tipografia: **Inter** (interface), números em **IBM Plex Mono**; títulos em Inter 600/700. Empacotadas localmente.
- Componentes shadcn: Button, Card, Badge, Dialog (guia), Sheet (definições), Tabs, Progress, Tooltip, Collapsible (detalhes nos cartões), ScrollArea, Separator, Input, Textarea, Checkbox, Switch, Slider, Skeleton.
- Ícones: lucide-react.
- Movimento: esvanecer escalonado na abertura e transições suaves entre ecrãs; respeita «reduzir movimento».

## 4. API (FastAPI, prefixo `/api`)

| Método | Caminho | Função |
|---|---|---|
| GET | `/health` | Estado |
| GET | `/datasets` | Conjuntos de demonstração |
| POST | `/analyses` | Analisar exemplo ou ficheiros carregados → resumo, pontos, zonas, superfície |
| GET | `/analyses/{id}/grid` | Grelha geofísica (ou derivada) em PNG + limites |
| POST | `/analyses/{id}/chat` | Pergunta ao assistente (offline ou Cloudflare) |
| GET | `/analyses/{id}/report.pdf`, `/samples.csv` | Exportações |
| GET | `/reference/provinces` | Províncias de Angola (base offline) |
| GET | `/terravisao/results`, `/terravisao/results/{id}` | Lista e detalhe |
| GET | `/terravisao/results/{id}/layer` | Camada em PNG + limites |
| GET | `/terravisao/results/{id}/report.pdf`, `/data.zip` | Exportações |
| POST | `/terravisao/validate` | Validar terreno |
| POST | `/terravisao/jobs`, GET `/terravisao/jobs/{id}` | Análise nova em segundo plano, com progresso |

A mesma aplicação FastAPI serve o frontend compilado (`frontend/dist`) em `/`.
