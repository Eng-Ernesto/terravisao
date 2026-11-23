# 01 — Visão do produto

## 1. Resumo

TerraVisão é uma plataforma web que recebe um terreno em Angola e devolve, em minutos, um mapa de probabilidade de ocorrência de **ferro, cobre, ouro e água subterrânea**, mais um relatório simples com recomendações de onde levar o trabalho de campo.

## 2. Problema

Saber se um terreno tem potencial mineral ou hídrico obriga hoje a enviar equipas ao campo sem garantia de retorno. O custo inicial (tempo, combustível, equipamento, mão de obra) leva cooperativas, pequenos investidores e empresas a desistir da prospecção.

## 3. Proposta de valor

- Reduz o custo inicial da prospecção.
- Reduz o tempo de análise preliminar de semanas para minutos.
- Direcciona o campo para as zonas de maior potencial.
- Usa apenas dados oficiais e públicos, sem equipamento caro na fase inicial.

## 4. Público-alvo

| Perfil | Necessidade principal |
|---|---|
| Geofísicos e geólogos | Priorizar alvos antes de planear magnetometria/resistividade |
| Cooperativas mineiras | Decidir se vale a pena investir em campo |
| Pequenos investidores | Avaliação rápida e barata de um terreno |
| Empresas de prospecção de água | Escolher onde fazer furos |
| Instituições | Avaliar terrenos com critério uniforme |

## 5. Âmbito do MVP

O sistema faz exactamente três coisas.

1. **Recebe o terreno** — desenho do polígono no mapa ou coordenadas.
2. **Analisa automaticamente** com Sentinel-2, Landsat, SRTM e mapas geológicos públicos.
3. **Entrega o resultado** — mapa de óxido de ferro, mapa de alteração argilosa, mapa de elevação/falhas/bacias, e classificação final Alta / Média / Baixa.

## 6. Fora do âmbito (não faz)

- Não confirma com certeza que existe mineral no subsolo.
- Não substitui o trabalho de campo do geofísico nem a sondagem (furo).
- Não faz análise química de amostras.
- Não usa dados geofísicos de campo (magnetometria, radiometria, resistividade) — ficam para fases posteriores.
- Sem contas de utilizador, pagamentos ou multi-tenant no MVP.

**O MVP é uma ferramenta de triagem:** indica onde vale a pena ir confirmar.

## 7. Exemplo de uso

1. O utilizador escolhe um terreno na Huíla.
2. O sistema detecta forte óxido de ferro e alteração argilosa nas imagens.
3. Cruza com o mapa geológico: a rocha é favorável.
4. Resultado: "Probabilidade Alta para ferro. Recomenda-se magnetometria no campo na Zona A."
5. O geofísico vai só à Zona A confirmar com magnetometria e resistividade.

## 8. Métricas de sucesso do MVP

| Métrica | Meta inicial |
|---|---|
| Tempo de análise de um terreno de 10 km² | ≤ 5 min |
| Terrenos de teste com resultado coerente com o geofísico | ≥ 3 áreas conhecidas (ex.: Longonjo) avaliadas e discutidas |
| Utilizadores-piloto que dizem que o relatório os ajudou a decidir | ≥ 5 |
| Custo de licenças e infra | 0 (tiers gratuitos) |

## 9. Princípios

1. **Honestidade científica:** toda a saída mostra que é probabilidade, com incerteza e limitações.
2. **Dados abertos primeiro:** só fontes gratuitas e com licença clara.
3. **Simples antes de sofisticado:** pontuação ponderada e explicável antes de modelos opacos.
4. **Explicável:** cada classe Alta/Média/Baixa deve poder ser justificada camada a camada.
