import shutil

import pytest
import yaml

from observatorio.catalog import CatalogError, load_catalog
from tests.conftest import REPO


def test_repo_catalog_is_valid():
    cat = load_catalog(REPO / "catalog")
    assert "wb_wdi" in cat.datasets
    assert len(cat.groups["G.ALC_CEPAL33"].miembros) == 33
    assert cat.geo_name("MEX") == "México"


def test_broken_reference_is_reported(tmp_path):
    root = tmp_path / "catalog"
    shutil.copytree(REPO / "catalog", root)
    path = root / "indicators" / "dem.yaml"
    docs = yaml.safe_load(path.read_text())
    docs[0]["concepto"] = "dem.no_existe"
    path.write_text(yaml.safe_dump(docs, allow_unicode=True))
    with pytest.raises(CatalogError, match="concepto desconocido"):
        load_catalog(root)


def test_unknown_group_member_is_reported(tmp_path):
    root = tmp_path / "catalog"
    shutil.copytree(REPO / "catalog", root)
    path = root / "geographies" / "grupos.yaml"
    docs = yaml.safe_load(path.read_text())
    docs[0]["miembros"].append("XXX")
    path.write_text(yaml.safe_dump(docs, allow_unicode=True))
    with pytest.raises(CatalogError, match="miembro desconocido 'XXX'"):
        load_catalog(root)
