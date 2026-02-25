"""
Construct a FLUX prompt from avatar fields + scene description.
Called by the BullMQ worker before each Replicate API call.
"""


def build_avatar_prompt(avatar: dict, scene_description: str) -> str:
    """
    Combine avatar fields (name, age, gender, nationality, physical_description)
    with the LLM-provided scene description to form a photorealistic FLUX prompt.

    Args:
        avatar: Full avatar dict from DB (may include None values for new fields).
        scene_description: Scene/pose/setting from the LLM send_photo tool call.

    Returns:
        Complete FLUX prompt string for Replicate.
    """
    name = avatar.get("name") or "woman"
    gender = avatar.get("gender") or "woman"
    age = avatar.get("age") or 25
    nationality = avatar.get("nationality") or ""
    appearance = avatar.get("physical_description") or ""

    parts: list[str] = [f"Photo of {name},"]

    if nationality:
        parts.append(f"a {age}-year-old {nationality} {gender},")
    else:
        parts.append(f"a {age}-year-old {gender},")

    if appearance:
        parts.append(appearance.rstrip(",") + ",")

    parts.append(scene_description.rstrip(",") + ",")

    # Quality anchors for photorealism
    parts.extend([
        "photorealistic, professional photography,",
        "high detail, natural lighting",
    ])

    return " ".join(parts)
