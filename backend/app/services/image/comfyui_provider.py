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
from pathlib import Path

import httpx

from app.config import settings
from app.services.image.base import GeneratedImage

logger = logging.getLogger(__name__)

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
        if not settings.comfyui_api_key:
            raise RuntimeError("COMFYUI_API_KEY is not set in .env")

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)
        ) as client:
            if reference_image_url:
                workflow, output_node = await self._build_i2i(
                    client, prompt, reference_image_url
                )
            else:
                workflow, output_node = self._build_t2i(prompt)

            prompt_id = await self._submit(client, workflow)
            image_bytes = await self._poll_and_download(client, prompt_id, output_node)

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
        resp = await client.post(
            f"{settings.comfyui_base_url}/api/prompt",
            json={"prompt": workflow},
            headers=self._headers(),
        )
        if resp.is_error:
            logger.error(f"ComfyUI submit error {resp.status_code}: {resp.text}")
        resp.raise_for_status()
        data = resp.json()
        prompt_id = data.get("prompt_id") or data.get("id")
        if not prompt_id:
            raise RuntimeError(f"ComfyUI did not return a prompt_id: {data}")
        logger.info(f"ComfyUI job submitted: {prompt_id}")
        return prompt_id

    async def _poll_and_download(
        self, client: httpx.AsyncClient, prompt_id: str, output_node: str
    ) -> bytes:
        """Poll /api/job/{id}/status until completed, then fetch history and download."""
        elapsed = 0.0
        while elapsed < POLL_TIMEOUT:
            await asyncio.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL

            resp = await client.get(
                f"{settings.comfyui_base_url}/api/job/{prompt_id}/status",
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")
            logger.debug(f"ComfyUI job {prompt_id} status: {status}")

            if status == "completed":
                return await self._fetch_history_and_download(
                    client, prompt_id, output_node
                )
            if status in ("failed", "cancelled", "canceled"):
                raise RuntimeError(
                    f"ComfyUI job {status}: {data.get('error') or data}"
                )

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
        for attempt in range(1, max_retries + 1):
            hist_resp = await client.get(
                f"{settings.comfyui_base_url}/api/history_v2/{prompt_id}",
                headers=self._headers(),
            )
            hist_resp.raise_for_status()
            history_data = hist_resp.json()

            # ComfyUI Cloud history_v2 wraps data under the prompt_id key
            job_data = history_data.get(prompt_id, {})
            outputs = job_data.get("outputs", {})

            if outputs:
                return await self._download_output(client, outputs, output_node)
            logger.warning(
                f"ComfyUI history_v2 outputs empty (attempt {attempt}/{max_retries})"
                f" for job {prompt_id} — retrying. Raw keys: {list(history_data.keys())}"
            )
            await asyncio.sleep(POLL_INTERVAL)

        raise RuntimeError(
            f"ComfyUI history_v2 returned empty outputs after {max_retries} retries"
            f" for job {prompt_id}"
        )

    async def _download_output(
        self, client: httpx.AsyncClient, outputs: dict, output_node: str
    ) -> bytes:
        """Extract filename from outputs dict and download the image."""
        node_out = outputs.get(output_node, {})
        images = node_out.get("images", [])
        if not images:
            # Log full outputs so we can debug node key mismatches
            logger.error(
                f"No images in output node '{output_node}'. "
                f"Available output nodes: {list(outputs.keys())}"
            )
            raise RuntimeError(
                f"ComfyUI: no images found in output node '{output_node}'. "
                f"Available nodes: {list(outputs.keys())}"
            )

        img_meta = images[0]
        filename = img_meta["filename"]
        subfolder = img_meta.get("subfolder", "")

        view_resp = await client.get(
            f"{settings.comfyui_base_url}/api/view",
            params={"filename": filename, "subfolder": subfolder, "type": "output"},
            headers=self._headers(),
            follow_redirects=True,
        )
        if view_resp.is_error:
            logger.error(f"ComfyUI view error {view_resp.status_code}: {view_resp.text}")
        view_resp.raise_for_status()
        logger.info(f"Downloaded {len(view_resp.content)} bytes from ComfyUI output")
        return view_resp.content
