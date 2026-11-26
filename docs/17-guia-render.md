# 17 — Guia: publicar no Render (link público, plano gratuito)

Para ter um link partilhável (`https://....onrender.com`) sem configurar servidor. Usa o mesmo `Dockerfile` do [guia Docker](13-guia-docker.md) — nada de novo para manter.

> **Plano gratuito, duas limitações a aceitar:**
> 1. **Adormece ao fim de 15 min sem visitas** e demora ~30-60 s a acordar na visita seguinte. Abra o link uns minutos antes de apresentar.
> 2. **O disco não é permanente.** Uma análise nova feita no TerraVisão («Nova análise») desaparece quando o serviço reinicia. Os exemplos incluídos na imagem (Longonjo, Lubango, os dois conjuntos de terras raras) **não são afectados** — ficam sempre disponíveis, porque vêm dentro da imagem, não do disco.
>
> Não testado ainda nesta conta Render; o build (Node + Python/GDAL) pode demorar 5 a 15 minutos na primeira vez.

## 1. Criar a conta

1. Abra https://render.com e crie uma conta (o mais rápido é "Sign up with GitHub", sem precisar de cartão para o plano gratuito).
2. Autorize o Render a aceder ao repositório `Eng-Ernesto/terravisao` (pode autorizar só esse, não é preciso dar acesso a todos).

## 2. Publicar com o Blueprint

O repositório já tem um `render.yaml` na raiz, por isso o Render configura tudo sozinho:

1. No painel do Render, **New +** → **Blueprint**.
2. Escolha o repositório `terravisao`.
3. O Render lê o `render.yaml` e mostra um serviço chamado `geoexplora-ia`, plano **Free**. Confirme com **Apply**.
4. Espere o build terminar (acompanhe os logs no painel). No fim aparece o link, algo como `https://geoexplora-ia.onrender.com`.

Se preferir não usar o Blueprint: **New +** → **Web Service** → escolha o repositório → Runtime **Docker** → deixe o `Dockerfile` por defeito → plano **Free** → **Create Web Service**.

## 3. Verificar

Abra o link. Deve ver a abertura animada do GeoExplora IA. Se mostrar erro ou página em branco:

| Sintoma | Causa provável |
|---|---|
| "Application failed to respond" | O build ainda não terminou, ou falhou — ver os logs no painel |
| Build falha a instalar `rasterio`/GDAL | Normalmente resolve-se sozinho (a imagem `python:3.12-slim` tem as bibliotecas de sistema necessárias); se persistir, copiar o erro dos logs |
| Demora muito a abrir da primeira vez | Normal: o serviço "acordou" (15 min sem acesso) |
| «Nova análise» no TerraVisão não aparece depois de recarregar a página mais tarde | Disco não é permanente no plano gratuito (ver aviso acima); os exemplos continuam lá |

## 4. Antes de apresentar

- Abra o link uns 5-10 minutos antes, para o serviço já estar "acordado".
- Se for uma apresentação longa, volte a abrir o link de vez em quando para não adormecer entre as pausas.
- Para a demonstração, use os exemplos prontos (Longonjo, Lubango, terras raras) em vez de depender de uma análise nova ao vivo — evita tanto a espera do download do Sentinel-2 como o risco de o resultado desaparecer se o serviço reiniciar.

## 5. Actualizar depois de alterações no código

O Render volta a fazer *build* sozinho sempre que há um novo commit em `main` (auto-deploy, activado por omissão no Blueprint). Não é preciso fazer mais nada além de `git push`.
