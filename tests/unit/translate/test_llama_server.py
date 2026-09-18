"""Gizli yerel llama.cpp sunucusunun yaşam döngüsü."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from src.contracts.errors import ModelMissingError, ProviderTimeout, ProviderUnavailable
from src.translate.llama_server import LlamaServer, _windows_process_baslat


class SahteSurec:
    def __init__(self, poll_sonucu: int | None = None, wait_hatasi: bool = False) -> None:
        self.poll_sonucu = poll_sonucu
        self.wait_hatasi = wait_hatasi
        self.terminate_sayisi = 0
        self.kill_sayisi = 0

    def poll(self) -> int | None:
        return self.poll_sonucu

    def terminate(self) -> None:
        self.terminate_sayisi += 1

    def wait(self, timeout: float | None = None) -> int:
        if self.wait_hatasi:
            raise subprocess.TimeoutExpired("llama", timeout)
        self.poll_sonucu = 0
        return 0

    def kill(self) -> None:
        self.kill_sayisi += 1


class SahteTasima:
    def __init__(self, saglik: list[bool] | None = None, cevap: object = None, hata: Exception | None = None) -> None:
        self.saglik = list(saglik or [True])
        self.cevap = cevap if cevap is not None else {"choices": [{"message": {"content": '{"translations":["x"]}'}}]}
        self.hata = hata
        self.getler: list[tuple[str, float]] = []
        self.postlar: list[tuple[str, dict[str, object], float]] = []

    def healthy(self, url: str, timeout: float) -> bool:
        self.getler.append((url, timeout))
        return self.saglik.pop(0) if self.saglik else True

    def post_json(self, url: str, payload: dict[str, object], timeout: float) -> object:
        self.postlar.append((url, payload, timeout))
        if self.hata is not None:
            raise self.hata
        return self.cevap


def dosyalar(tmp_path: Path) -> tuple[Path, Path]:
    exe, model = tmp_path / "llama-server.exe", tmp_path / "model.gguf"
    exe.write_bytes(b"exe")
    model.write_bytes(b"gguf")
    return exe, model


def test_windows_process_baslat_konsolu_ve_tum_akislari_gizler(monkeypatch: pytest.MonkeyPatch) -> None:
    kayit: dict[str, Any] = {}

    def sahte_popen(command: list[str], **kwargs: object) -> SahteSurec:
        kayit["command"], kayit["kwargs"] = command, kwargs
        return SahteSurec()

    monkeypatch.setattr(subprocess, "Popen", sahte_popen)
    _windows_process_baslat(["llama-server.exe", "--host", "127.0.0.1"])
    kwargs = kayit["kwargs"]
    assert kwargs["creationflags"] == getattr(subprocess, "CREATE_NO_WINDOW", 0)
    assert kwargs["stdin"] is subprocess.DEVNULL and kwargs["stdout"] is subprocess.DEVNULL and kwargs["stderr"] is subprocess.DEVNULL


def test_tembel_baslatir_loopback_sagligi_bekler_ve_chat_istegi_gonderir(tmp_path: Path) -> None:
    exe, model = dosyalar(tmp_path)
    surec = SahteSurec()
    komutlar: list[list[str]] = []
    tasima = SahteTasima([False, True])
    beklemeler: list[float] = []
    sunucu = LlamaServer(
        exe, model, port=18457, process_start=lambda komut: komutlar.append(komut) or surec,
        transport=tasima, waiter=beklemeler.append, startup_attempts=3,
    )

    sonuc = sunucu.complete("sistem", "kullanıcı", 321)

    assert sonuc == '{"translations":["x"]}'
    assert komutlar == [[str(exe), "-m", str(model), "--host", "127.0.0.1", "--port", "18457", "-ngl", "99", "-c", "4096", "--log-disable"]]
    assert beklemeler == [0.1]
    url, veri, _ = tasima.postlar[0]
    assert url == "http://127.0.0.1:18457/v1/chat/completions"
    assert veri["temperature"] == 0 and veri["max_tokens"] == 321
    assert veri["chat_template_kwargs"] == {"enable_thinking": False}
    assert veri["messages"] == [{"role": "system", "content": "sistem"}, {"role": "user", "content": "kullanıcı"}]


def test_goreli_dosya_yollari_surec_dizini_degisince_bozulmaz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    exe, model = dosyalar(tmp_path)
    monkeypatch.chdir(tmp_path)
    komutlar: list[list[str]] = []
    sunucu = LlamaServer(
        Path(exe.name), Path(model.name), port=18458,
        process_start=lambda komut: komutlar.append(komut) or SahteSurec(), transport=SahteTasima(),
    )

    sunucu.complete("s", "u", 10)

    assert komutlar[0][0] == str(exe.resolve())
    assert komutlar[0][2] == str(model.resolve())


def test_eksik_dosya_model_hatasi_surec_baslamaz(tmp_path: Path) -> None:
    baslatildi: list[bool] = []
    sunucu = LlamaServer(tmp_path / "yok.exe", tmp_path / "yok.gguf", process_start=lambda _k: baslatildi.append(True) or SahteSurec())
    with pytest.raises(ModelMissingError):
        sunucu.complete("s", "u", 10)
    assert baslatildi == []


def test_surec_sagliktan_once_cikarsa_kullanilamaz(tmp_path: Path) -> None:
    exe, model = dosyalar(tmp_path)
    sunucu = LlamaServer(exe, model, process_start=lambda _k: SahteSurec(7), transport=SahteTasima([False]), startup_attempts=1)
    with pytest.raises(ProviderUnavailable) as hata:
        sunucu.complete("secret", "source", 10)
    assert "secret" not in str(hata.value) and "source" not in str(hata.value)


def test_tasima_zaman_asimi_sinifini_korur(tmp_path: Path) -> None:
    exe, model = dosyalar(tmp_path)
    sunucu = LlamaServer(exe, model, process_start=lambda _k: SahteSurec(), transport=SahteTasima(hata=ProviderTimeout("slow")))
    with pytest.raises(ProviderTimeout):
        sunucu.complete("s", "u", 10)


@pytest.mark.parametrize("cevap", [{}, {"choices": []}, {"choices": [{"message": {"content": 4}}]}])
def test_bozuk_http_cevabi_kullanilamaz(cevap: object, tmp_path: Path) -> None:
    exe, model = dosyalar(tmp_path)
    sunucu = LlamaServer(exe, model, process_start=lambda _k: SahteSurec(), transport=SahteTasima(cevap=cevap))
    with pytest.raises(ProviderUnavailable):
        sunucu.complete("s", "u", 10)


def test_close_idempotent_sureci_sonlandirir_gerekirse_oldurur(tmp_path: Path) -> None:
    exe, model = dosyalar(tmp_path)
    surec = SahteSurec(wait_hatasi=True)
    sunucu = LlamaServer(exe, model, process_start=lambda _k: surec, transport=SahteTasima())
    sunucu.complete("s", "u", 10)
    sunucu.close()
    sunucu.close()
    assert surec.terminate_sayisi == 1 and surec.kill_sayisi == 1
