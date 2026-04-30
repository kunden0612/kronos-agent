import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports():
    try:
        from app.config import settings
        from app.services.data_fetcher import data_fetcher
        from app.services.kronos_predictor import kronos_predictor
        assert True
    except Exception as e:
        assert False, f"Import failed: {e}"


def test_settings():
    from app.config import settings
    assert settings.API_PORT == 8001
    assert settings.DEFAULT_MODEL == "NeoQuasar/Kronos-mini"


def test_data_fetcher_exists():
    from app.services.data_fetcher import data_fetcher
    assert data_fetcher is not None


def test_kronos_predictor_exists():
    from app.services.kronos_predictor import kronos_predictor
    assert kronos_predictor is not None


if __name__ == "__main__":
    test_imports()
    test_settings()
    test_data_fetcher_exists()
    test_kronos_predictor_exists()
    print("All tests passed!")
