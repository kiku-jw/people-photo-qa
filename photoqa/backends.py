"""Optional backend discovery."""

from __future__ import annotations

import importlib.metadata
import importlib.util


BACKEND_MODULES = {
    "pillow": "PIL",
    "opencv": "cv2",
    "mediapipe": "mediapipe",
    "insightface": "insightface",
    "deepface": "deepface",
    "openai": "openai",
}


def package_version(package_name: str) -> str | None:
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def backend_status() -> dict[str, dict[str, str | bool | None]]:
    status: dict[str, dict[str, str | bool | None]] = {}
    package_names = {
        "pillow": "Pillow",
        "opencv": "opencv-python",
        "mediapipe": "mediapipe",
        "insightface": "insightface",
        "deepface": "deepface",
        "openai": "openai",
    }
    for backend_name, module_name in BACKEND_MODULES.items():
        installed = importlib.util.find_spec(module_name) is not None
        status[backend_name] = {
            "installed": installed,
            "module": module_name,
            "version": package_version(package_names[backend_name]),
        }
    return status


def available_backend_names() -> list[str]:
    status = backend_status()
    return [name for name, item in status.items() if item["installed"]]


def missing_backend_names() -> list[str]:
    status = backend_status()
    return [name for name, item in status.items() if not item["installed"]]
