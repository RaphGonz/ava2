"""
ComfyUI Cloud image provider.
Uses two workflows:
  - text_to_image.json  : avatar reference image (no input image needed)
  - image_to_image.json : scene photo from reference image (Qwen Edit / FluxKontext)

API: cloud.comfy.org — X-API-Key auth, POST /api/prompt, poll GET /api/job/{id}/status,
     then GET /api/history_v2/{id} (returns {"{prompt_id}": {"outputs": {...}}}),
     download via GET /api/view?filename=...&subfolder=...&type=output.
"""
import asyncio
import copy
import json
import logging
import random
import sys
from pathlib import Path

import httpx

from app.config import settings
from app.services.image.base import GeneratedImage

logger = logging.getLogger(__name__)


def _dbg(msg: str) -> None:
    """Debug print that bypasses Python logging config — always visible in uvicorn stderr."""
    print(f"[COMFY_DBG] {msg}", flush=True, file=sys.stderr)
    logger.error(f"[COMFY_DBG] {msg}")

WORKFLOWS_DIR = Path(__file__).parent / "workflows"
POLL_INTERVAL = 4.0   # seconds between status checks
POLL_TIMEOUT = 300    # seconds before giving up


def _load_workflow(name: str) -> dict:
    """Load a workflow JSON from the workflows/ directory."""
    path = WORKFLOWS_DIR / f"{name}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class ComfyUIProvider:
    """
    Calls ComfyUI Cloud REST API.
    - generate(prompt)                        → text-to-image (avatar reference)
    - generate(prompt, reference_image_url=…) → image-to-image (scene photo)
    Satisfies ImageProvider Protocol via structural typing (ARCH-03).
    """

    def _headers(self) -> dict:
        return {"X-API-Key": settings.comfyui_api_key}

    async def generate(
        self,
        prompt: str,
        aspect_ratio: str = "2:3",
        reference_image_url: str | None = None,
    ) -> GeneratedImage:
        _dbg(f"generate() ENTERED. base_url={settings.comfyui_base_url!r} api_key_set={bool(settings.comfyui_api_key)}")
        if not settings.comfyui_api_key:
            raise RuntimeError("COMFYUI_API_KEY is not set in .env")

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)
        ) as client:
            _dbg("httpx.AsyncClient created")
            if reference_image_url:
                _dbg(f"building i2i workflow, ref_url={reference_image_url!r}")
                workflow, output_node = await self._build_i2i(
                    client, prompt, reference_image_url
                )
            else:
                _dbg("building t2i workflow")
                workflow, output_node = self._build_t2i(prompt)
            _dbg(f"workflow built, output_node={output_node!r}")

            _dbg("calling _submit()")
            prompt_id = await self._submit(client, workflow)
            _dbg(f"_submit() returned prompt_id={prompt_id!r}")

            _dbg(f"calling _poll_and_download() for prompt_id={prompt_id!r}")
            image_bytes = await self._poll_and_download(client, prompt_id, output_node)
            _dbg(f"_poll_and_download() returned {len(image_bytes)} bytes")

        _dbg("generate() returning GeneratedImage")
        return GeneratedImage(
            url="",
            model="comfyui-qwen",
            prompt=prompt,
            image_bytes=image_bytes,
        )

    # ------------------------------------------------------------------
    # Workflow builders
    # ------------------------------------------------------------------

    def _build_t2i(self, prompt: str) -> tuple[dict, str]:
        """Text-to-image: inject prompt and randomized seed into node 91/86:3."""
        workflow = copy.deepcopy(_load_workflow("text_to_image"))
        workflow["91"]["inputs"]["value"] = prompt
        # Randomize seed to ensure unique generation each call
        workflow["86:3"]["inputs"]["seed"] = random.randint(0, 2**32 - 1)
        return workflow, "60"

    async def _build_i2i(
        self, client: httpx.AsyncClient, prompt: str, reference_image_url: str
    ) -> tuple[dict, str]:
        """Image-to-image: upload reference image, inject prompt, randomize seed."""
        workflow = copy.deepcopy(_load_workflow("image_to_image"))
        ref_filename = await self._upload_image(client, reference_image_url)
        workflow["41"]["inputs"]["image"] = ref_filename
        workflow["89:68"]["inputs"]["prompt"] = prompt
        workflow["89:65"]["inputs"]["seed"] = random.randint(0, 2**32 - 1)
        return workflow, "9"

    # ------------------------------------------------------------------
    # API helpers
    # ------------------------------------------------------------------

    async def _upload_image(
        self, client: httpx.AsyncClient, image_url: str
    ) -> str:
        """Download image from URL and upload to ComfyUI Cloud input folder."""
        img_resp = await client.get(image_url)
        img_resp.raise_for_status()

        upload_resp = await client.post(
            f"{settings.comfyui_base_url}/api/upload/image",
            files={"image": ("reference.jpg", img_resp.content, "image/jpeg")},
            data={"type": "input", "overwrite": "true"},
            headers=self._headers(),
        )
        if upload_resp.is_error:
            logger.error(f"ComfyUI upload error {upload_resp.status_code}: {upload_resp.text}")
        upload_resp.raise_for_status()
        return upload_resp.json()["name"]

    async def _submit(self, client: httpx.AsyncClient, workflow: dict) -> str:
        """Submit workflow, return prompt_id."""
        submit_url = f"{settings.comfyui_base_url}/api/prompt"
        _dbg(f"_submit() POST {submit_url}")
        resp = await client.post(
            submit_url,
            json={"prompt": workflow},
            headers=self._headers(),
        )
        _dbg(f"_submit() response status={resp.status_code} body={resp.text[:500]!r}")
        if resp.is_error:
            logger.error(f"ComfyUI submit error {resp.status_code}: {resp.text}")
        resp.raise_for_status()
        data = resp.json()
        prompt_id = data.get("prompt_id") or data.get("id")
        if not prompt_id:
            raise RuntimeError(f"ComfyUI did not return a prompt_id: {data}")
        _dbg(f"_submit() prompt_id={prompt_id!r}")
        logger.info(f"ComfyUI job submitted: {prompt_id}")
        return prompt_id

    async def _poll_and_download(
        self, client: httpx.AsyncClient, prompt_id: str, output_node: str
    ) -> bytes:
        """Poll /api/job/{id}/status until completed, then fetch history and download."""
        status_url = f"{settings.comfyui_base_url}/api/job/{prompt_id}/status"
        _dbg(f"_poll_and_download() starting. prompt_id={prompt_id!r} poll_url={status_url!r} interval={POLL_INTERVAL}s timeout={POLL_TIMEOUT}s")
        elapsed = 0.0
        iteration = 0
        while elapsed < POLL_TIMEOUT:
            _dbg(f"[POLL iter={iteration}] sleeping {POLL_INTERVAL}s (elapsed={elapsed:.1f}s)")
            await asyncio.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL
            iteration += 1

            _dbg(f"[POLL iter={iteration}] GET {status_url}")
            resp = await client.get(
                status_url,
                headers=self._headers(),
            )
            _dbg(f"[POLL iter={iteration}] response http_status={resp.status_code} body={resp.text[:800]!r}")
            resp.raise_for_status()
            data = resp.json()

            # Log every key in the response so we can detect wrong field names
            _dbg(f"[POLL iter={iteration}] parsed JSON keys={list(data.keys())} full={json.dumps(data)[:600]}")

            status = data.get("status")
            _dbg(f"[POLL iter={iteration}] data.get('status')={status!r}")

            if status in ("completed", "success"):
                _dbg(f"[POLL iter={iteration}] status={status!r} -> fetching history")
                return await self._fetch_history_and_download(
                    client, prompt_id, output_node
                )
            # ComfyUI Cloud API failure statuses: "error" (API docs), "failed",
            # "cancelled", "canceled". Without this check, a failed job would poll
            # indefinitely until POLL_TIMEOUT (300s) instead of failing fast.
            if status in ("error", "failed", "cancelled", "canceled"):
                raise RuntimeError(
                    f"ComfyUI job {status}: {data.get('error') or data.get('error_message') or data}"
                )
            _dbg(f"[POLL iter={iteration}] status={status!r} not terminal — continuing poll")

        _dbg(f"_poll_and_download() TIMEOUT after {POLL_TIMEOUT}s ({iteration} iterations)")
        raise TimeoutError(f"ComfyUI job timed out after {POLL_TIMEOUT}s")

    async def _fetch_history_and_download(
        self,
        client: httpx.AsyncClient,
        prompt_id: str,
        output_node: str,
        max_retries: int = 3,
    ) -> bytes:
        """
        GET /api/history_v2/{prompt_id} to retrieve output node filenames.
        ComfyUI Cloud returns: { "{prompt_id}": { "outputs": {...}, "status": {...} } }
        Retries up to max_retries times when outputs are empty (race condition).
        Then downloads via GET /api/view.
        """
        hist_url = f"{settings.comfyui_base_url}/api/history_v2/{prompt_id}"
        _dbg(f"_fetch_history_and_download() ENTERED. prompt_id={prompt_id!r} url={hist_url!r}")
        for attempt in range(1, max_retries + 1):
            _dbg(f"[HIST attempt={attempt}/{max_retries}] GET {hist_url}")
            hist_resp = await client.get(
                hist_url,
                headers=self._headers(),
            )
            _dbg(f"[HIST attempt={attempt}] http_status={hist_resp.status_code} body={hist_resp.text[:800]!r}")
            hist_resp.raise_for_status()
            history_data = hist_resp.json()
            _dbg(f"[HIST attempt={attempt}] top-level keys={list(history_data.keys())}")

            # ComfyUI Cloud history_v2 wraps data under the prompt_id key
            job_data = history_data.get(prompt_id, {})
            _dbg(f"[HIST attempt={attempt}] job_data keys={list(job_data.keys())}")
            outputs = job_data.get("outputs", {})
            _dbg(f"[HIST attempt={attempt}] outputs keys={list(outputs.keys())}")

            if outputs:
                _dbg(f"[HIST attempt={attempt}] outputs non-empty -> calling _download_output()")
                return await self._download_output(client, outputs, output_node)
            logger.warning(
                f"ComfyUI history_v2 outputs empty (attempt {attempt}/{max_retries})"
                f" for job {prompt_id} — retrying. Raw keys: {list(history_data.keys())}"
            )
            _dbg(f"[HIST attempt={attempt}] outputs empty, sleeping {POLL_INTERVAL}s before retry")
            await asyncio.sleep(POLL_INTERVAL)

        _dbg(f"_fetch_history_and_download() FAILED after {max_retries} retries")
        raise RuntimeError(
            f"ComfyUI history_v2 returned empty outputs after {max_retries} retries"
            f" for job {prompt_id}"
        )

    async def _download_output(
        self, client: httpx.AsyncClient, outputs: dict, output_node: str
    ) -> bytes:
        """Extract filename from outputs dict and download the image."""
        _dbg(f"_download_output() ENTERED. output_node={output_node!r} outputs_keys={list(outputs.keys())}")
        node_out = outputs.get(output_node, {})
        _dbg(f"_download_output() node_out keys={list(node_out.keys()) if isinstance(node_out, dict) else type(node_out)}")
        images = node_out.get("images", [])
        _dbg(f"_download_output() images count={len(images)} first={repr(images[0]) if images else None}")
        if not images:
            # Log full outputs so we can debug node key mismatches
            logger.error(
                f"No images in output node '{output_node}'. "
                f"Available output nodes: {list(outputs.keys())}"
            )
            _dbg(f"_download_output() ERROR: no images in node '{output_node}'. Available: {list(outputs.keys())}")
            raise RuntimeError(
                f"ComfyUI: no images found in output node '{output_node}'. "
                f"Available nodes: {list(outputs.keys())}"
            )

        img_meta = images[0]
        filename = img_meta["filename"]
        subfolder = img_meta.get("subfolder", "")
        view_url = f"{settings.comfyui_base_url}/api/view"
        _dbg(f"_download_output() GET {view_url} filename={filename!r} subfolder={subfolder!r}")

        view_resp = await client.get(
            view_url,
            params={"filename": filename, "subfolder": subfolder, "type": "output"},
            headers=self._headers(),
            follow_redirects=True,
        )
        _dbg(f"_download_output() view response http_status={view_resp.status_code} content_length={len(view_resp.content)}")
        if view_resp.is_error:
            logger.error(f"ComfyUI view error {view_resp.status_code}: {view_resp.text}")
        view_resp.raise_for_status()
        logger.info(f"Downloaded {len(view_resp.content)} bytes from ComfyUI output")
        _dbg(f"_download_output() returning {len(view_resp.content)} bytes")
        return view_resp.content
