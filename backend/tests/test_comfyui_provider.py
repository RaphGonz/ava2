"""
Unit tests for ComfyUIProvider — covers the 4-step API flow, seed randomization,
Protocol compliance, and history retry logic.
All HTTP calls are mocked via unittest.mock.AsyncMock — no live COMFYUI_API_KEY needed.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
from unittest.mock import Mock


# ---------------------------------------------------------------------------
# Helpers — build mock httpx responses
# ---------------------------------------------------------------------------

def _mock_response(json_data=None, content=None, status_code=200):
    """Build a mock httpx.Response object."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.is_error = status_code >= 400
    if json_data is not None:
        resp.json = MagicMock(return_value=json_data)
    if content is not None:
        resp.content = content
    resp.raise_for_status = MagicMock()  # no-op (success assumed by default)
    return resp


# ---------------------------------------------------------------------------
# Test: Text-to-image generates image bytes via 4-step flow
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_t2i_generate_returns_image_bytes():
    """
    Full t2i path (no reference_image_url):
      1. POST /api/prompt  → {"prompt_id": "test-t2i-id"}
      2. GET /api/job/test-t2i-id/status  → {"status": "completed"}
      3. GET /api/history_v2/test-t2i-id  → outputs with filename out.png
      4. GET /api/view  → b"fakepngbytes"
    Assert: result.image_bytes == b"fakepngbytes", result.model == "comfyui-qwen"
    """
    from app.services.image.comfyui_provider import ComfyUIProvider

    submit_resp = _mock_response(json_data={"prompt_id": "test-t2i-id"})
    status_resp = _mock_response(json_data={"status": "completed"})
    history_resp = _mock_response(json_data={
        "outputs": {
            "60": {
                "images": [{"filename": "out.png", "subfolder": "", "type": "output"}]
            }
        }
    })
    view_resp = _mock_response(content=b"fakepngbytes")

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=submit_resp)

    get_call_count = 0

    async def mock_get(url, **kwargs):
        nonlocal get_call_count
        get_call_count += 1
        if "status" in url:
            return status_resp
        if "history_v2" in url:
            return history_resp
        if "view" in url:
            return view_resp
        raise ValueError(f"Unexpected GET: {url}")

    mock_client.get = mock_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    provider = ComfyUIProvider()

    with patch("app.services.image.comfyui_provider.httpx.AsyncClient", return_value=mock_client), \
         patch("app.config.settings.comfyui_api_key", "test-key"), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        result = await provider.generate("a beautiful avatar")

    assert result.image_bytes == b"fakepngbytes"
    assert result.model == "comfyui-qwen"


# ---------------------------------------------------------------------------
# Test: Image-to-image generates image bytes via 4-step flow with upload
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_i2i_generate_returns_image_bytes():
    """
    Full i2i path (reference_image_url provided):
      1. GET reference_url  → b"refimgbytes"
      2. POST /api/upload/image  → {"name": "reference.jpg"}
      3. POST /api/prompt  → {"prompt_id": "test-i2i-id"}
      4. GET /api/job/test-i2i-id/status  → {"status": "completed"}
      5. GET /api/history_v2/test-i2i-id  → outputs with filename edit.png
      6. GET /api/view  → b"editimgbytes"
    Assert: result.image_bytes == b"editimgbytes"
    """
    from app.services.image.comfyui_provider import ComfyUIProvider

    ref_resp = _mock_response(content=b"refimgbytes")
    ref_resp.content = b"refimgbytes"
    ref_resp.raise_for_status = MagicMock()

    upload_resp = _mock_response(json_data={"name": "reference.jpg"})
    submit_resp = _mock_response(json_data={"prompt_id": "test-i2i-id"})
    status_resp = _mock_response(json_data={"status": "completed"})
    history_resp = _mock_response(json_data={
        "outputs": {
            "9": {
                "images": [{"filename": "edit.png", "subfolder": "", "type": "output"}]
            }
        }
    })
    view_resp = _mock_response(content=b"editimgbytes")

    post_call_index = 0

    async def mock_post(url, **kwargs):
        nonlocal post_call_index
        if "upload/image" in url:
            return upload_resp
        if "prompt" in url:
            return submit_resp
        raise ValueError(f"Unexpected POST: {url}")

    async def mock_get(url, **kwargs):
        if "http://ref.example.com" in url:
            return ref_resp
        if "status" in url:
            return status_resp
        if "history_v2" in url:
            return history_resp
        if "view" in url:
            return view_resp
        raise ValueError(f"Unexpected GET: {url}")

    mock_client = AsyncMock()
    mock_client.post = mock_post
    mock_client.get = mock_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    provider = ComfyUIProvider()

    with patch("app.services.image.comfyui_provider.httpx.AsyncClient", return_value=mock_client), \
         patch("app.config.settings.comfyui_api_key", "test-key"), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        result = await provider.generate(
            "a beautiful scene",
            reference_image_url="http://ref.example.com/avatar.jpg"
        )

    assert result.image_bytes == b"editimgbytes"


# ---------------------------------------------------------------------------
# Test: Seed is randomized across calls (no HTTP needed)
# ---------------------------------------------------------------------------

def test_seed_is_randomized_across_calls():
    """
    Call _build_t2i twice and confirm the seed values differ.
    Tests that random.randint is used (not a hardcoded constant from JSON).
    """
    from app.services.image.comfyui_provider import ComfyUIProvider

    provider = ComfyUIProvider()
    workflow1, _ = provider._build_t2i("test prompt")
    workflow2, _ = provider._build_t2i("test prompt")

    seed1 = workflow1["86:3"]["inputs"]["seed"]
    seed2 = workflow2["86:3"]["inputs"]["seed"]

    # Seeds must differ (with overwhelming probability for 32-bit random values)
    assert seed1 != seed2, (
        f"Seeds should be different across calls but both were {seed1}"
    )


# ---------------------------------------------------------------------------
# Test: ComfyUIProvider satisfies ImageProvider Protocol
# ---------------------------------------------------------------------------

def test_protocol_compliance():
    """
    ComfyUIProvider must be an instance of ImageProvider (structural typing).
    """
    from app.services.image.base import ImageProvider
    from app.services.image.comfyui_provider import ComfyUIProvider

    provider = ComfyUIProvider()
    assert isinstance(provider, ImageProvider), (
        "ComfyUIProvider does not satisfy ImageProvider Protocol"
    )


# ---------------------------------------------------------------------------
# Test: History retry on empty outputs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_history_retry_on_empty_outputs():
    """
    _fetch_history_and_download must retry if first history response has empty outputs.
    Mock sequence:
      - status GET → {"status": "completed"}
      - history_v2 GET #1 → {"outputs": {}}  (empty — race condition)
      - history_v2 GET #2 → {"outputs": {"60": {"images": [...]}}}  (success)
      - view GET → b"retrybytes"
    Assert: result.image_bytes == b"retrybytes"
    """
    from app.services.image.comfyui_provider import ComfyUIProvider

    submit_resp = _mock_response(json_data={"prompt_id": "retry-test-id"})
    status_resp = _mock_response(json_data={"status": "completed"})

    history_empty = _mock_response(json_data={"outputs": {}})
    history_full = _mock_response(json_data={
        "outputs": {
            "60": {
                "images": [{"filename": "retry.png", "subfolder": "", "type": "output"}]
            }
        }
    })
    view_resp = _mock_response(content=b"retrybytes")

    history_call_count = 0

    async def mock_get(url, **kwargs):
        nonlocal history_call_count
        if "status" in url:
            return status_resp
        if "history_v2" in url:
            history_call_count += 1
            if history_call_count == 1:
                return history_empty
            return history_full
        if "view" in url:
            return view_resp
        raise ValueError(f"Unexpected GET: {url}")

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=submit_resp)
    mock_client.get = mock_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    provider = ComfyUIProvider()

    with patch("app.services.image.comfyui_provider.httpx.AsyncClient", return_value=mock_client), \
         patch("app.config.settings.comfyui_api_key", "test-key"), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        result = await provider.generate("retry test prompt")

    assert result.image_bytes == b"retrybytes"
    assert history_call_count == 2, (
        f"Expected 2 history_v2 calls (retry), got {history_call_count}"
    )
