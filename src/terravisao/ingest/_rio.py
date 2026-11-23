"""Configuração de leitura remota de COGs (AWS S3 público) partilhada pelas fontes.

Medido em Longonjo: ler uma banda passou de ~9 s para ~0,4 s com estas opções
(evita listar o directório do bucket e multiplexa pedidos HTTP/2).
"""

from __future__ import annotations

GDAL_OPTIONS = {
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif,.tiff",
    "GDAL_HTTP_MULTIPLEX": "YES",
    "GDAL_HTTP_VERSION": "2",
    "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES",
    "VSI_CACHE": "TRUE",
    "GDAL_INGESTED_BYTES_AT_OPEN": "32768",
}


def configure() -> None:
    import odc.stac

    odc.stac.configure_rio(cloud_defaults=True, aws={"aws_unsigned": True}, **GDAL_OPTIONS)  # type: ignore[arg-type]
