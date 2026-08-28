"""Deterministic, dependency-light audit for Android navigation screenshots.

The script intentionally reports measurable signals only. It does not claim visual
conformance with the UIX references without a supplied baseline for the same viewport.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def luminance(rgb: tuple[int, int, int]) -> float:
    values = []
    for channel in rgb:
        value = channel / 255
        values.append(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4)
    return 0.2126 * values[0] + 0.7152 * values[1] + 0.0722 * values[2]


def contrast(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    first, second = sorted((luminance(a), luminance(b)))
    return (second + 0.05) / (first + 0.05)


def inspect(path: Path) -> dict:
    try:
        from PIL import Image
    except ImportError:
        return {"file": path.name, "status": "SKIPPED", "reason": "Pillow no instalado"}

    image = Image.open(path).convert("RGB")
    width, height = image.size
    pixels = image.load()
    samples = [pixels[x, y] for y in range(0, height, max(1, height // 12)) for x in range(0, width, max(1, width // 8))]
    background = samples[0]
    distinct = len({tuple(channel // 16 for channel in sample) for sample in samples})
    near_uniform = sum(1 for sample in samples if sum(abs(sample[i] - background[i]) for i in range(3)) < 12)
    # A flat or nearly empty screenshot is a strong diagnostic signal, not a visual verdict.
    return {
        "file": path.name,
        "status": "OK",
        "width": width,
        "height": height,
        "aspect_ratio": round(width / height, 4) if height else None,
        "sampled_color_bins": distinct,
        "near_uniform_samples": near_uniform,
        "possible_blank_or_loading": distinct <= 2,
        "contrast_proxy": "not_measurable_without_text/layout bounds",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    files = sorted(args.evidence_dir.glob("*.png"))
    report = {
        "evidence_dir": str(args.evidence_dir),
        "screenshots": [inspect(path) for path in files],
        "summary": {
            "count": len(files),
            "blank_or_loading": 0,
            "low_contrast": "not_measurable_without_text/layout bounds",
            "missing_evidence": not bool(files),
        },
        "limitations": [
            "La captura no permite demostrar por sí sola que un botón haya respondido; eso lo cubre el test semántico.",
            "La detección de imágenes rotas requiere inspección del árbol Compose o un baseline de recursos; no se infiere de píxeles.",
            "La conformidad UIX requiere comparar cada pantalla con una referencia del mismo viewport.",
        ],
    }
    report["summary"]["blank_or_loading"] = sum(1 for item in report["screenshots"] if item.get("possible_blank_or_loading"))
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
