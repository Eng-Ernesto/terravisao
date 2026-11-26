# 18 — Guia: publicar no Azure App Service (com créditos gratuitos)

Alternativa ao [Render](17-guia-render.md), recomendada se já tem uma conta Azure com créditos. Vantagem sobre o plano gratuito do Render: **não "adormece"** entre visitas, o que é mais seguro durante uma apresentação ao vivo. Usa o mesmo `Dockerfile` do [guia Docker](13-guia-docker.md) — nada de novo para manter.

> Não testado ainda nesta conta. Evite o nível **F1 (Grátis)**: tem uma quota diária de minutos de CPU muito curta, insuficiente para uma análise real (download de Sentinel-2, GDAL). Use **B1 (Básico)** — os seus créditos cobrem isto confortavelmente durante o evento.

## 1. Criar o serviço (App Service, contentor Docker)

1. No [portal Azure](https://portal.azure.com), **Criar um recurso** → **Web App**.
2. Na aba **Básico**:
   - **Grupo de recursos:** criar um novo (ex.: `geoexplora-rg`).
   - **Nome:** um nome único — vai dar o link `https://<nome>.azurewebsites.net`.
   - **Publicar:** **Contentor Docker**.
   - **Sistema operativo:** Linux.
   - **Plano do App Service:** criar novo, SKU **B1 Básico** (não o F1 Grátis).
3. Na aba **Docker**:
   - **Opções:** Contentor único.
   - **Origem da imagem:** **GitHub Actions** (a Azure cria sozinha um workflow que builda o `Dockerfile` do repositório a cada `git push` e publica).
   - Autorize o acesso ao GitHub e escolha o repositório `Eng-Ernesto/terravisao`, ramo `main`. A Azure detecta o `Dockerfile` na raiz automaticamente.
4. **Rever + criar** → **Criar**. A primeira construção (Node + Python/GDAL) demora uns 5 a 15 minutos — acompanhe em **Actions** no GitHub ou em **Centro de Implementação** no portal.

## 2. Um ajuste obrigatório: a porta

A Azure assume por omissão que o contentor escuta na porta 80; a nossa app escuta na **8501**. Sem isto, o link fica "a carregar" para sempre:

1. No recurso criado, **Configuração** → **Definições de aplicação** → **Nova definição de aplicação**.
2. Nome: `WEBSITES_PORT`, Valor: `8501` → **Guardar** → **Continuar** (reinicia sozinho).

(`TERRAVISAO_CACHE_DIR` e `GEOEXPLORA_ROOT` já vêm definidos dentro da imagem — não é preciso repeti-los aqui.)

## 3. Verificar

Abra `https://<nome>.azurewebsites.net`. Deve ver a abertura animada do GeoExplora IA.

| Sintoma | Causa provável |
|---|---|
| Fica "a carregar" / erro 502 | `WEBSITES_PORT` não está definido como 8501, ou o build ainda não terminou |
| Build falha no GitHub Actions | Ver o log do passo que falhou em **Actions** no GitHub; normalmente é a instalação do GDAL/rasterio, que costuma resolver-se sozinha na imagem `python:3.12-slim` |
| Demora mais de 230 s a responder na primeira vez | A Azure corta ligações que não respondem em 230 s; a nossa app arranca em segundos, por isso isto indicaria um problema no arranque — ver **Registo do Contentor** em **Monitorização** |
| Uma análise nova no TerraVisão desaparece depois de reiniciar | O disco do contentor não é permanente entre reinícios (igual ao Docker/Render); os exemplos incluídos na imagem não são afectados |

## 4. Antes de apresentar

- Ao contrário do Render gratuito, o B1 **não adormece** sozinho — pode abrir o link a qualquer momento sem esperar.
- Use os exemplos prontos (Longonjo, Lubango, terras raras) como base da demonstração; uma análise nova ao vivo depende de internet e de alguns minutos de download do Sentinel-2.

## 5. Actualizar depois de alterações no código

Como a origem é **GitHub Actions**, basta `git push` para `main`: a Azure reconstrói e publica sozinha.

## 6. Quando os créditos acabarem

Lembre-se de **apagar o grupo de recursos** (`geoexplora-rg`) se decidir não continuar com o serviço, para não ser cobrado depois de os créditos gratuitos expirarem.
