# pylint: disable=missing-docstring
import json
import logging
import tempfile
from pathlib import Path

import pytest

from mlc_chat.support.auto_config import detect_config

logging.basicConfig(
    level=logging.INFO,
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S",
    format="{asctime} {levelname} {filename}:{lineno}: {message}",
)


def _create_json_file(json_path, data):
    with open(json_path, "w", encoding="utf-8") as i_f:
        json.dump(data, i_f)


def test_detect_config():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        config_json_path = base_path / "config.json"
        _create_json_file(config_json_path, {})

        assert detect_config(base_path) == config_json_path
        assert detect_config(config_json_path) == config_json_path


def test_detect_config_fail():
    with pytest.raises(ValueError):
        detect_config(Path("do/not/exist"))

    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        with pytest.raises(ValueError):
            assert detect_config(base_path)


if __name__ == "__main__":
    test_detect_config()
    test_detect_config_fail()
