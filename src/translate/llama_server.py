"""Yerel llama.cpp sunucusunu konsolsuz ve yalnız loopback üzerinde çalıştırır."""
from __future__ import annotations

import json
import socket
import subprocess
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Protocol, cast

from src.contracts.errors import ModelMissingError, ProviderTimeout, ProviderUnavailable, TranslatorError

__all__ = ["LlamaServer"]


class ProcessHandle(Protocol):
    def poll(self) -> int | None: ...
    def terminate(self) -> None: ...
    def wait(self, timeout: float | None = None) -> int: ...
    def kill(self) -> None: ...


class HttpTransport(Protocol):
    def healthy(self, url: str, timeout: float) -> bool: ...
    def post_json(self, url: str, payload: dict[str, object], timeout: float) -> object: ...


def _windows_process_baslat(command: Sequence[str]) -> ProcessHandle:
    return subprocess.Popen(
        list(command),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        cwd=str(Path(command[0]).resolve().parent),
    )


def _bos_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soket:
        soket.bind(("127.0.0.1", 0))
        return int(soket.getsockname()[1])


class _StdlibTransport:
    def healthy(self, url: str, timeout: float) -> bool:
        try:
            with urllib.request.urlopen(url, timeout=timeout) as cevap:  # noqa: S310 -- sabit loopback URL
                return int(cevap.status) == 200
        except (OSError, urllib.error.URLError):
            return False

    def post_json(self, url: str, payload: dict[str, object], timeout: float) -> object:
        istek = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(istek, timeout=timeout) as cevap:  # noqa: S310 -- sabit loopback URL
                ham = cevap.read(2 * 1024 * 1024)
        except (TimeoutError, socket.timeout) as e:
            raise ProviderTimeout("yerel kalite motoru zaman aşımına uğradı") from e
        except (OSError, urllib.error.URLError) as e:
            raise ProviderUnavailable(f"yerel kalite motoruna ulaşılamadı: {type(e).__name__}") from e
        try:
            return json.loads(ham)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ProviderUnavailable("yerel kalite motoru geçerli HTTP JSON döndürmedi") from e


class LlamaServer:
    """llama-server sürecini ilk istekte başlatan ``ChatClient`` uygulaması."""

    def __init__(
        self,
        executable: Path,
        model: Path,
        *,
        port: int | None = None,
        process_start: Callable[[Sequence[str]], ProcessHandle] | None = None,
        transport: HttpTransport | None = None,
        waiter: Callable[[float], None] = time.sleep,
        startup_attempts: int = 150,
        request_timeout: float = 45.0,
    ) -> None:
        if startup_attempts < 1 or request_timeout <= 0:
            raise ValueError("startup_attempts >= 1 ve request_timeout > 0 olmalı")
        self._executable = Path(executable).resolve()
        self._model = Path(model).resolve()
        self._port = int(port if port is not None else _bos_port())
        self._process_start = process_start or _windows_process_baslat
        self._transport = transport or _StdlibTransport()
        self._waiter = waiter
        self._startup_attempts = startup_attempts
        self._request_timeout = request_timeout
        self._process: ProcessHandle | None = None
        self._hazir = False
        self._kapali = False

    def _baslat(self) -> None:
        if self._kapali:
            raise ProviderUnavailable("yerel kalite motoru kapatıldı")
        if self._hazir:
            return
        eksik = [p.name for p in (self._executable, self._model) if not p.is_file()]
        if eksik:
            raise ModelMissingError(f"yerel kalite motoru dosyaları eksik: {', '.join(eksik)}")
        komut = [
            str(self._executable), "-m", str(self._model), "--host", "127.0.0.1", "--port", str(self._port),
            "-ngl", "99", "-c", "4096", "--log-disable",
        ]
        try:
            self._process = self._process_start(komut)
        except Exception as e:
            raise ProviderUnavailable(f"yerel kalite motoru başlatılamadı: {type(e).__name__}") from e
        saglik = f"http://127.0.0.1:{self._port}/health"
        for deneme in range(self._startup_attempts):
            if self._process.poll() is not None:
                raise ProviderUnavailable("yerel kalite motoru hazır olmadan kapandı")
            if self._transport.healthy(saglik, 0.2):
                self._hazir = True
                return
            if deneme + 1 < self._startup_attempts:
                self._waiter(0.1)
        raise ProviderTimeout("yerel kalite motoru başlangıç zaman aşımına uğradı")

    def complete(self, system: str, user: str, max_tokens: int) -> str:
        self._baslat()
        veri: dict[str, object] = {
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0,
            "seed": 0,
            "max_tokens": int(max_tokens),
            "chat_template_kwargs": {"enable_thinking": False},
            "response_format": {"type": "json_object"},
        }
        try:
            cevap = self._transport.post_json(
                f"http://127.0.0.1:{self._port}/v1/chat/completions", veri, self._request_timeout
            )
        except TranslatorError:
            raise
        except Exception as e:
            raise ProviderUnavailable(f"yerel kalite motoru isteği başarısız: {type(e).__name__}") from e
        try:
            kok = cast(dict[str, Any], cevap)
            icerik = kok["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderUnavailable("yerel kalite motoru beklenmeyen HTTP şeması döndürdü") from e
        if not isinstance(icerik, str):
            raise ProviderUnavailable("yerel kalite motoru metin içerik döndürmedi")
        return icerik

    def close(self) -> None:
        if self._kapali:
            return
        self._kapali = True
        surec, self._process = self._process, None
        if surec is None or surec.poll() is not None:
            return
        surec.terminate()
        try:
            surec.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            surec.kill()
