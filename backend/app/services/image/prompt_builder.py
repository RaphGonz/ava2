"""
Construct a FLUX/ComfyUI prompt from avatar fields + scene description.
Called by the BullMQ worker before each ComfyUI API call, and by the
reference-image endpoint in avatars.py.
"""


def build_avatar_prompt(avatar: dict, scene_description: str) -> str:
    """
    Combine avatar fields (name, age, gender, nationality, physical_description)
    with the LLM-provided scene description to form a photorealistic ComfyUI prompt.

    Always includes a full-body composition directive so ComfyUI generates
    the avatar from head to toe, not a portrait/face crop.

    Args:
        avatar: Full avatar dict from DB (may include None values for new fields).
        scene_description: Scene/pose/setting from the LLM send_photo tool call
                           or from the reference-image endpoint.

    Returns:
        Complete prompt string for ComfyUI.
    """
    name = avatar.get("name") or "woman"
    gender = avatar.get("gender") or "woman"
    age = avatar.get("age") or 25
    nationality = avatar.get("nationality") or ""
    appearance = avatar.get("physical_description") or ""

    # Safety prefix — keeps model in professional editorial mode without implying portrait crop
    parts: list[str] = [
        "Professional photograph, fully clothed, editorial style,",
        f"photo of {name},",
    ]

    if nationality:
        parts.append(f"a {age}-year-old {nationality} {gender},")
    else:
        parts.append(f"a {age}-year-old {gender},")

    if appearance:
        parts.append(appearance.rstrip(",") + ",")

    parts.append(scene_description.rstrip(",") + ",")

    # Composition directive — selfie scenes get a close-up framing,
    # everything else defaults to full-body
    _selfie_keywords = {"selfie", "self-portrait", "self portrait", "phone camera", "front camera"}
    is_selfie = any(kw in scene_description.lower() for kw in _selfie_keywords)

    if is_selfie:
        parts.append(
            "selfie, close-up shot, upper body framing, arm extended holding phone,"
            " slight downward angle, smartphone camera, candid, natural expression,"
        )
    else:
        parts.append("full body, standing, full-length portrait, head to toe,")

    # Quality anchors for photorealism
    parts.extend([
        "photorealistic, professional photography,",
        "high detail, natural lighting, SFW",
    ])

    return " ".join(parts)
