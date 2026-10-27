"""Shared constants for the OpenAI image plugin."""

GENERATE_TOOL_NAME = "openai_image_generate"
EDIT_TOOL_NAME = "openai_image_edit"
POLISH_TOOL_NAME = "openai_image_polish_prompt"

# Template key stamped on source entries for the declarative settings page.
TEMPLATE_KEY = "openai_compatible"

POLISH_SYSTEM_PROMPT = (
    "You are an expert prompt engineer for text-to-image models. Rewrite the "
    "user's image request into a single, vivid, production-ready image generation "
    "prompt. Preserve the original intent and any text that must appear in the "
    "image. Include subject, composition, style, lighting, camera angle, colors, "
    "level of detail, and mood when appropriate. Return only the polished prompt, "
    "without explanations, quotes, labels, or markdown."
)

# Keys whose string value directly holds image data (URL / base64 / data URI).
IMAGE_URL_KEYS = (
    "b64_json",
    "base64",
    "image_base64",
    "url",
    "image_url",
    "image",
)
# Container keys that may wrap a list of image entries.
IMAGE_CONTAINER_KEYS = ("data", "images", "result", "output")
