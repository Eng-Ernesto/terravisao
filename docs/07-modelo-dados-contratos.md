# 07 — Modelo de dados e contratos

Contratos entre módulos. Escritos como esboço em Python (`dataclass`/Pydantic); a implementação pode ajustar nomes mantendo a semântica.

## 1. Entrada

```python
class Target(str, Enum):
    IRON = "ferro"
    COPPER = "cobre"
    GOLD = "ouro"
    WATER = "agua"


@dataclass
class AnalysisRequest:
    geometry: dict  # GeoJSON Polygon/MultiPolygon, WGS84
    targets: list[Target]
    date_from: date | None  # defeito: época seca dos últimos 2-3 anos
    date_to: date | None
    max_cloud_pct: float = 20.0
    weights_override: dict | None = None  # só utilizadores avançados
    name: str | None = None
```

Validações (módulo `aoi`):
- geometria válida e não vazia;
- dentro dos limites de Angola (polígono de fronteira em `data/reference/`);
- área ≤ `MAX_AREA_KM2`;
- pelo menos um alvo.

## 2. Camadas

```python
@dataclass
class Layer:
    name: str  # "iron_oxide", "clay", "slope", ...
    array: np.ndarray  # 2D float32, NaN onde inválido
    transform: Affine
    crs: str  # EPSG do UTM da AOI
    valid_fraction: float  # 0-1
    source: str  # "sentinel2", "srtm", "geology"...
    unit: str | None
    status: Literal["ok", "partial", "unavailable"]
    note: str | None = None
```

Todas as camadas partilham a mesma grelha (CRS, transform, shape) antes do `scoring`.

## 3. Saída

```python
@dataclass
class Zone:
    id: str  # "A", "B", ...
    target: Target
    geometry: dict  # GeoJSON, WGS84
    area_km2: float
    mean_score: float
    max_score: float
    contributions: dict[str, float]  # camada -> contribuição média
    recommendation: str


@dataclass
class TargetResult:
    target: Target
    final_class: Literal["baixa", "media", "alta"]
    confidence: Literal["baixa", "media", "alta"]
    score_layer: Layer  # raster de pontuação 0-1
    class_layer: Layer  # raster 0/1/2
    area_by_class_km2: dict[str, float]
    zones: list[Zone]


@dataclass
class AnalysisResult:
    request: AnalysisRequest
    thematic_layers: dict[str, Layer]  # óxido de ferro, argila, elevação, ...
    lineaments: dict  # GeoJSON
    basins: dict  # GeoJSON
    targets: dict[Target, TargetResult]
    provenance: Provenance
    warnings: list[str]
```

```python
@dataclass
class Provenance:
    pipeline_version: str
    created_at: datetime
    scenes: dict[str, list[str]]  # fonte -> ids de cenas
    config_snapshot: dict  # pesos, limiares, parâmetros
    layer_quality: dict[str, float]  # valid_fraction por camada
```

## 4. Interfaces dos módulos

```python
# ingest
def fetch_sentinel2(aoi, date_from, date_to, max_cloud) -> BandStack | Unavailable
def fetch_landsat(aoi, date_from, date_to, max_cloud) -> BandStack | Unavailable
def fetch_dem(aoi) -> Raster | Unavailable
def fetch_geology(aoi) -> GeoDataFrame | Unavailable

# indices
def iron_oxide(stack) -> Layer
def ferrous(stack) -> Layer
def clay(stack) -> Layer
def ndvi(stack) -> Layer

# terrain
def slope(dem) -> Layer
def hillshade_multi(dem) -> Layer
def lineaments(dem) -> tuple[GeoJSON, Layer]   # linhas + densidade
def drainage(dem) -> tuple[Layer, GeoJSON]     # acumulação + linhas
def basins(dem) -> GeoJSON
def twi(dem) -> Layer

# geology
def lithology_favorability(gdf, target, rules) -> Layer

# scoring
def score(layers: dict[str, Layer], weights: dict[str, float]) -> Layer
def classify(score: Layer, thresholds) -> Layer
def final_class(class_layer, zones, rules) -> str
def confidence(layers: dict[str, Layer]) -> str

# zones
def extract_zones(class_layer, score_layer, layers, target) -> list[Zone]

# report
def render_maps(result) -> dict[str, Path]
def build_pdf(result, out_path) -> Path
def export_geotiff(layer, path) -> Path
def export_geojson(zones, path) -> Path

# pipeline
def run(request, progress_cb=None) -> AnalysisResult
```

`Unavailable(reason: str)` é um valor, não excepção: o pipeline segue e regista aviso.

## 5. Configuração

`config.yaml` (ou `config.py`), versionado:

```yaml
max_area_km2: 2500
grid_resolution_m: 20
season_months: [5, 6, 7, 8, 9]
ndvi_mask: 0.4
percentiles: [2, 98]
thresholds: { media: 0.40, alta: 0.65 }
min_zone_area_km2: 0.5
weights:
  ferro: { iron_oxide: 0.35, ferrous: 0.10, clay: 0.10, lithology: 0.30, lineament_density: 0.10, slope_inv: 0.05 }
  cobre: { ... }
  ouro:  { ... }
  agua:  { ... }
```

Os valores de `weights` e `thresholds` são pontos de partida a calibrar (doc 05).

## 6. Ficheiros de referência

| Ficheiro | Conteúdo |
|---|---|
| `data/reference/angola_boundary.geojson` | Fronteira para validação |
| `data/reference/litologia_regras.csv` | Unidade/litologia → favorabilidade por alvo |
| `data/reference/recomendacoes.csv` | Alvo → método de campo |
| `data/reference/test_areas.geojson` | Áreas de teste (Longonjo, Huíla, …) |

## 7. Formato de exportação

- **GeoTIFF:** `score_<alvo>.tif` (float32, 0–1, CRS UTM da AOI), `class_<alvo>.tif` (uint8).
- **GeoJSON:** `zones_<alvo>.geojson` com propriedades de `Zone`.
- **JSON:** `run.json` com `Provenance` e `AnalysisRequest`.
- **PDF:** `relatorio_<nome>_<data>.pdf`.
