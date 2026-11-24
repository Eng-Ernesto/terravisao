# 13 — Guia: executar o GeoExplora IA com Docker

Para correr a demonstração noutro computador. **Só a primeira vez precisa de internet** (para construir a imagem). Depois, a demonstração funciona sem ligação.

> **Estado:** o Dockerfile ainda **não foi testado** (o computador de desenvolvimento não tem Docker). Este guia é também o roteiro de validação: siga os passos e a lista da secção 7 e diga o que falhou.

## 1. O que precisa

| Item | Detalhe |
|---|---|
| Docker Desktop | Windows 10/11, macOS ou Linux (no Linux, Docker Engine + Compose) |
| Memória | 4 GB livres (8 GB no total é confortável) |
| Disco | cerca de 3 GB para a imagem |
| Internet | só no passo 3 (descarregar base e dependências). Opcional depois |
| Git | opcional (pode descarregar o ZIP) |

## 2. Instalar o Docker Desktop

**Windows:** instale o Docker Desktop (https://www.docker.com/products/docker-desktop/), aceite a opção **WSL 2** e reinicie. Abra o Docker Desktop e espere até o ícone indicar *Engine running*.

Confirme num terminal (PowerShell):

```powershell
docker --version
docker compose version
```

Se o Docker diz que a virtualização está desligada, active-a na BIOS (Intel VT-x / AMD-V).

## 3. Obter o projecto e construir

Com **git**:

```powershell
git clone https://github.com/Eng-Ernesto/terravisao.git
cd terravisao
```

Se o repositório ainda for privado, é preciso ter acesso à conta e iniciar sessão (`gh auth login`), ou pedir o ZIP. **Sem git:** em https://github.com/Eng-Ernesto/terravisao, botão *Code → Download ZIP*, extraia e abra o terminal nessa pasta.

Construir e arrancar (**precisa de internet; demora 5 a 15 minutos na primeira vez**):

```powershell
docker compose up --build
```

Está pronto quando aparecer uma linha como `You can now view your Streamlit app in your browser`.

## 4. Abrir a aplicação

No navegador: **http://localhost:8501**

Deve ver o **GeoExplora IA** com o módulo **Análise de mapa**: amostras de Longonjo sobre imagem de satélite, classes de anomalia, a tabela de zonas e o painel do **Assistente** à direita. No menu à esquerda, escolha o conjunto «modelo sintético coerente» e experimente o módulo **TerraVisão (satélite)** (resultados de Longonjo e Lubango).

## 5. Testar offline (importante para a apresentação)

1. Pare com `Ctrl+C` no terminal (ou `docker compose down`).
2. **Desligue o Wi-Fi / cabo de rede.**
3. Arranque sem reconstruir:

```powershell
docker compose up
```

4. Abra http://localhost:8501 e confirme:
   - os mapas aparecem, com imagem de satélite e linhas das províncias (sem mosaicos online);
   - trocar de alvo (Ferro, Cobre, Ouro, Água) e de camada funciona;
   - o botão **Relatório (PDF)** descarrega um PDF.

Sem internet, a opção «Nova análise» mostra um aviso e não consegue descarregar imagens novas. Os exemplos continuam disponíveis em «Resultados».

## 6. Roteiro de apresentação

O roteiro completo está em [15-roteiro-demonstracao.md](15-roteiro-demonstracao.md). Resumo (5 minutos):

1. **Problema:** equipas de campo sem saber se o terreno vale a pena.
2. **Resultados → Longonjo:** mostrar o mapa, a classe e as zonas A e B. Explicar que é **triagem**, não prova de minério.
3. **Camadas:** imagem de satélite, óxido de ferro, argila, relevo.
4. **Lubango (Huíla):** outro terreno, com probabilidade mais alta para cobre, ouro e água.
5. **Relatório (PDF):** descarregar e abrir.
6. **Com internet (opcional):** «Nova análise» → desenhar um terreno → analisar (cerca de 1 a 3 minutos).

## 7. Lista de validação (preencher e enviar)

- [ ] `docker compose up --build` terminou sem erros. Tempo: ____ min
- [ ] http://localhost:8501 abre e mostra «Análise de mapa» (dados da equipa)
- [ ] «Modelo sintético coerente» mostra uma zona A e o modelo «supera o acaso»
- [ ] Os botões do Assistente respondem (offline) e a resposta aparece no topo do painel
- [ ] «Relatório técnico (PDF)» descarrega e abre
- [ ] Módulo TerraVisão: Longonjo e Lubango abrem
- [ ] Mapa com imagem de satélite (sem internet)
- [ ] Texto com as fontes certas (títulos com serifa); se aparecerem letras «normais», avisar
- [ ] Dados (zip) descarrega
- [ ] Sem internet: tudo acima continua a funcionar
- [ ] Com internet: TerraVisão → «Nova análise», desenhar e analisar funciona
- [ ] (Opcional) Assistente com IA: o token tem de ter permissão para o Workers AI. Coloque o Account ID e o token em «Assistente de IA (opcional)» e pergunte algo. Esperado: resposta em 3 a 8 s com «Com IA (Cloudflare Workers AI)» no painel; se falhar, a resposta automática indica o motivo (token inválido, quota esgotada, sem internet)
- [ ] Computador, sistema e memória: ____________________

## 8. Parar, retomar e actualizar

```powershell
docker compose down
docker compose up
```

Para receber alterações novas do projecto:

```powershell
git pull
docker compose up --build
```

## 9. Levar sem internet (imagem em ficheiro)

Se o computador da apresentação nunca terá internet, construa a imagem num computador com internet e leve-a em ficheiro.

No computador com internet:

```powershell
docker compose build
docker save terravisao:dev -o terravisao.tar
```

No computador da apresentação (copie `terravisao.tar` e o ficheiro `docker-compose.yml`):

```powershell
docker load -i terravisao.tar
docker compose up
```

O `docker-compose.yml` usa a imagem `terravisao:dev`; sem a pasta do projecto, edite-o e retire a linha `build: .`.

## 10. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `docker: command not found` | Docker não instalado ou terminal antigo | Reinstalar, abrir novo terminal |
| «Docker Desktop is starting…» para sempre | WSL 2 / virtualização desligada | Activar virtualização na BIOS; `wsl --update` |
| `port is already allocated` | Porta 8501 ocupada | No `docker-compose.yml`, trocar `8501:8501` por `8502:8501` e abrir `localhost:8502` |
| Fica «Killed» ou muito lento | Pouca memória | Docker Desktop → Settings → Resources → Memory: 4 GB ou mais |
| Mapa vazio, sem satélite | Terreno sem imagem RGB | Os exemplos incluídos têm; refazer a análise |
| «Nova análise» falha | Sem internet ou falha da fonte | Ligar à internet; tentar de novo |
| Letras diferentes das capturas | Fontes não carregaram | Recarregar a página (Ctrl+F5) e avisar |

## 11. Limitações conhecidas

- Imagem **não testada** até agora em Docker.
- Resultados de demonstração com pontuação relativa à área e sem mapa geológico: servem para mostrar o funcionamento, não como prospecção.
- Análises novas precisam de internet e gravam em `data/cache/runs/` (pasta partilhada com o contentor).
