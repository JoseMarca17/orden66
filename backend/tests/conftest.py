"""Fixtures compartidas de las pruebas del núcleo."""

import pytest
from orden66.backend.core import config
from orden66.backend.core.models import Calendario, Pelicula, Sala


@pytest.fixture
def calendario():
    return Calendario.crear(
        [Sala(s.id, s.capacidad, s.formatos) for s in config.SALAS],
        [Pelicula(*p) for p in config.PELICULAS_BASE],
    )
