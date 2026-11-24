# Documentação — TerraVisão (MVP)

## Ordem de leitura

1. **Quem quer perceber o produto:** 01 → 09
2. **Quem vai implementar:** 03 → 04 → 05 → 07 → 08
3. **Quem vai desenhar a interface:** 02 → 06 → 12
4. **Quem vai validar a ciência (geofísicos):** 05 → 09 → 10
5. **Quem vai apresentar ou testar a demonstração:** 13

## Convenções

- Idioma: português (Angola). Código, nomes de variáveis e de ficheiros: inglês.
- Requisitos têm ID estável: `RF-xx` (funcional), `RNF-xx` (não funcional), `US-xx` (história). Tarefas do backlog referenciam estes IDs.
- Valores marcados com **[A CALIBRAR]** são propostas iniciais que devem ser validadas por um geofísico antes de serem tratadas como definitivas.
- Itens marcados com **[A VERIFICAR]** são pressupostos sobre fontes de dados que precisam de ser confirmados antes de implementar.

## Resumo numa página

| Item | Decisão |
|---|---|
| Entrada | Polígono desenhado no mapa, coordenadas ou ficheiro GeoJSON/KML |
| Dados | Sentinel-2, Landsat 8/9, SRTM, mapa geológico (OneGeology) |
| Alvos | Ferro, cobre, ouro, água subterrânea |
| Método | Índices espectrais + terreno + litologia → pontuação multicritério ponderada → classe Alta/Média/Baixa |
| Saída | Mapas (óxido de ferro, argila, elevação/falhas/bacias, probabilidade), zonas priorizadas, relatório PDF |
| Interface | Streamlit |
| Custo de licenças | Zero |
| Natureza | Triagem. Não confirma presença de mineral |
