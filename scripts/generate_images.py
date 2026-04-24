from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "manga_config.json"
API_URL = "https://api.openai.com/v1/images/generations"
EDIT_API_URL = "https://api.openai.com/v1/images/edits"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def call_image_api(api_key: str, payload: dict) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error {exc.code}: {body}") from exc


def build_multipart(fields: dict[str, str], image_paths: list[Path]) -> tuple[bytes, str]:
    boundary = f"----codex-manga-{uuid.uuid4().hex}"
    chunks: list[bytes] = []

    def add_line(value: str | bytes = "") -> None:
        if isinstance(value, str):
            chunks.append(value.encode("utf-8"))
        else:
            chunks.append(value)
        chunks.append(b"\r\n")

    for key, value in fields.items():
        add_line(f"--{boundary}")
        add_line(f'Content-Disposition: form-data; name="{key}"')
        add_line()
        add_line(value)

    for path in image_paths:
        content_type = mimetypes.guess_type(path.name)[0] or "image/png"
        add_line(f"--{boundary}")
        add_line(f'Content-Disposition: form-data; name="image[]"; filename="{path.name}"')
        add_line(f"Content-Type: {content_type}")
        add_line()
        chunks.append(path.read_bytes())
        chunks.append(b"\r\n")

    add_line(f"--{boundary}--")
    return b"".join(chunks), boundary


def call_image_edit_api(api_key: str, fields: dict[str, str], reference_paths: list[Path]) -> dict:
    data, boundary = build_multipart(fields, reference_paths)
    request = urllib.request.Request(
        EDIT_API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error {exc.code}: {body}") from exc


def save_image_response(response: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data_items = response.get("data") or []
    if not data_items:
        raise RuntimeError("No image data returned from API")

    first = data_items[0]
    if "b64_json" in first:
        output_path.write_bytes(base64.b64decode(first["b64_json"]))
        return

    if "url" in first:
        with urllib.request.urlopen(first["url"], timeout=300) as image_response:
            output_path.write_bytes(image_response.read())
        return

    raise RuntimeError(f"Unsupported image response shape: {first.keys()}")


def build_payload(config: dict, prompt: str, model_override: str | None) -> dict:
    return {
        "model": model_override or config["model"],
        "prompt": prompt,
        "size": config["size"],
        "quality": config["quality"],
        "output_format": config["output_format"],
        "n": 1,
    }


def selected_reference_items(config: dict, reference_keys: list[str] | None = None) -> list[dict]:
    items = config.get("reference_images", [])
    if reference_keys is None:
        return items
    selected = []
    keys = set(reference_keys)
    for item in items:
        if item["key"] in keys:
            selected.append(item)
    missing = keys - {item["key"] for item in selected}
    if missing:
        raise RuntimeError(f"Unknown reference key(s): {', '.join(sorted(missing))}")
    return selected


def reference_paths(config: dict, reference_keys: list[str] | None = None) -> list[Path]:
    paths = []
    for item in selected_reference_items(config, reference_keys):
        path = ROOT / item["path"]
        if not path.exists():
            raise FileNotFoundError(f"Reference image missing: {path}")
        paths.append(path)
    return paths


def build_reference_prompt_prefix(config: dict, reference_keys: list[str] | None = None) -> str:
    items = selected_reference_items(config, reference_keys)
    lines = [
        "Attached reference image order. Treat these as the strict character design canon:",
    ]
    for index, item in enumerate(items, start=1):
        lines.append(f"{index}. {item['role']} ({item['key']})")
    lines.append("Use these exact designs for every matching character. Do not invent alternate costumes, hairstyles, faces, or armor.")
    lines.append("Do not swap character identities. If a reference image is not attached for this job, do not introduce that character.")
    return "\n".join(lines)


def generate_one(
    config: dict,
    prompt_path: Path,
    output_path: Path,
    model_override: str | None,
    dry_run: bool,
    use_references: bool,
    reference_keys: list[str] | None,
) -> None:
    prompt = read_prompt(prompt_path)
    refs = reference_paths(config, reference_keys) if use_references else []
    prompt_with_refs = f"{build_reference_prompt_prefix(config, reference_keys)}\n\n{prompt}" if refs else prompt
    payload = build_payload(config, prompt_with_refs, model_override)
    if dry_run:
        print(
            json.dumps(
                {
                    "prompt_file": str(prompt_path),
                    "output_file": str(output_path),
                    "endpoint": "edits" if refs else "generations",
                    "reference_images": [str(path.relative_to(ROOT)) for path in refs],
                    "payload": payload,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing. Put it in .env or set it in the environment.")

    if refs:
        fields = {key: str(value) for key, value in payload.items()}
        response = call_image_edit_api(api_key, fields, refs)
    else:
        response = call_image_api(api_key, payload)
    save_image_response(response, output_path)
    print(f"Wrote {output_path.relative_to(ROOT)}")


def parse_page_selection(value: str) -> list[int]:
    pages: set[int] = set()
    for chunk in value.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            start, end = chunk.split("-", 1)
            pages.update(range(int(start), int(end) + 1))
        else:
            pages.add(int(chunk))
    return sorted(pages)


def parse_character_selection(value: str, available: list[dict]) -> list[dict]:
    if value.strip().lower() == "all":
        return available
    selected = {item.strip().lower() for item in value.split(",") if item.strip()}
    jobs = [item for item in available if item["key"].lower() in selected]
    missing = selected - {item["key"].lower() for item in jobs}
    if missing:
        raise RuntimeError(f"Unknown character key(s): {', '.join(sorted(missing))}")
    return jobs


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate manga images with the OpenAI Images API.")
    parser.add_argument("--cover", action="store_true", help="Generate the cover image.")
    parser.add_argument("--characters", help="Character sheets to generate: all or comma-separated keys such as mai,akari,grave.")
    parser.add_argument("--pages", help="Page numbers to generate, for example: 1,3,5-8")
    parser.add_argument("--prompt", help="Generate one arbitrary prompt markdown file.")
    parser.add_argument("--output", help="Output file for --prompt.")
    parser.add_argument("--model", help="Override model name, for example gpt-image-1.5 if gpt-image-2 is unavailable.")
    parser.add_argument("--no-references", action="store_true", help="Do not send images/reference files to the edits endpoint.")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without calling the API.")
    parser.add_argument("--sleep", type=float, default=1.0, help="Seconds to wait between API calls.")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    config = load_json(CONFIG_PATH)
    manifest_path = ROOT / config["production_dir"] / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("production/manifest.json is missing. Run: python scripts/prepare_manga.py")
    manifest = load_json(manifest_path)

    jobs: list[tuple[Path, Path, bool, list[str] | None]] = []
    use_refs = bool(config.get("use_reference_images", False)) and not args.no_references
    if args.cover:
        jobs.append(
            (
                ROOT / manifest["assets"]["cover_prompt"],
                ROOT / config["images_dir"] / f"cover.{config['output_format']}",
                use_refs,
                manifest["assets"].get("cover_reference_keys"),
            )
        )

    if args.characters:
        for character in parse_character_selection(args.characters, manifest.get("characters", [])):
            jobs.append((ROOT / character["prompt_file"], ROOT / character["output_file"], False, None))

    if args.pages:
        selected = set(parse_page_selection(args.pages))
        for page in manifest["pages"]:
            if page["page"] in selected:
                jobs.append((ROOT / page["prompt_file"], ROOT / page["output_file"], use_refs, page.get("reference_keys")))

    if args.prompt:
        if not args.output:
            raise RuntimeError("--output is required when --prompt is used.")
        jobs.append((ROOT / args.prompt, ROOT / args.output, use_refs, None))

    if not jobs:
        parser.print_help()
        return 2

    for index, (prompt_path, output_path, job_uses_refs, reference_keys) in enumerate(jobs, start=1):
        if not prompt_path.exists():
            raise FileNotFoundError(prompt_path)
        print(f"[{index}/{len(jobs)}] {prompt_path.relative_to(ROOT)}")
        generate_one(config, prompt_path, output_path, args.model, args.dry_run, job_uses_refs, reference_keys)
        if not args.dry_run and index < len(jobs):
            time.sleep(args.sleep)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
