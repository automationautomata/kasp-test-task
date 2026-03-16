import asyncio
from io import BytesIO

import pandas as pd
import pytest
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response

from app import setup
from app.config import AppConfig
from app.handlers import router


@pytest.fixture(scope="session")
def test_config():
    return AppConfig(
        _env_file=None,
        db_dsn="sqlite+aiosqlite:///:memory:",
        lemmas_cache_maxsize=1000,
        writer_chunk_size=8192,
        max_workers=4,
        upload_chunk_size_mb=1,
        max_uploading_users=10,
        workers_type="threads",
        file_uploading_limit_gb=None,
    )


@pytest.fixture(scope="session")
def test_engine(test_config):
    engine = setup.db_engine(test_config.db_dsn)
    asyncio.run(setup.init_db(engine))
    return engine


@pytest.fixture(scope="session")
def test_container(test_config, test_engine):
    return setup.container(test_config, test_engine)


@pytest.fixture
def client(test_container):

    app = FastAPI()
    app.include_router(router)
    setup_dishka(test_container, app)
    return TestClient(app)


@pytest.mark.parametrize(
    "text_content,lemmas_total_number,word_lemma,total_word_count",
    [
        (
            "Тут русский текст\n"
            "Еще русский текст, \n"
            "Снова русский текст, \n"
            "По приказу острых козырьков - тут еще русский текст",
            9,
            "текст",
            4,
        ),
        (
            "",
            0,
            None,
            0,
        ),
    ],
)
def test_export_statistics(
    client, text_content, lemmas_total_number, word_lemma, total_word_count
):
    file_data = BytesIO(text_content.encode("utf-8"))
    file_data.name = "test.txt"

    resp: Response = client.post(
        "/public/report/export", files={"file": ("ex.txt", file_data, "text/plain")}
    )

    assert resp.status_code == 200

    content = b"".join(resp.iter_bytes())

    # Проверка, что это XLSX-файл
    assert content.startswith(b"PK\x03\x04")

    df = pd.read_excel(BytesIO(content))

    valid_headers = {"словоформа", "кол-во", "кол-во по строкам"}
    assert set(df.keys()) == valid_headers

    cols_sizes = {len(df[k]) for k in valid_headers}
    assert len(cols_sizes) == 1 and lemmas_total_number in cols_sizes

    if word_lemma:
        assert word_lemma in set(df["словоформа"])

        lemma_row_ind = list(df["словоформа"]).index(word_lemma)
        assert df["кол-во"][lemma_row_ind] == total_word_count
