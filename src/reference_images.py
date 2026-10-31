"""Read edit reference images without trusting URLs from message content."""

from __future__ import annotations

import asyncio
import base64
import binascii
import ipaddress
import re
import socket
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

import aiohttp
from PIL import Image as PILImage
from yarl import URL

from astrbot.api import logger
from astrbot.api.message_components import Image
from astrbot.core.utils.astrbot_path import get_astrbot_data_path

from .response_utils import split_image_value

MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
DOWNLOAD_TIMEOUT = 15
ATTACHMENT_TIMEOUT = 20
MAX_REDIRECTS = 2
SUPPORTED_FORMATS = ("PNG", "JPEG", "WEBP", "GIF", "BMP")
ALLOWED_PORTS = (80, 443, 8080, 8443)


class ReferenceImageError(ValueError):
    """A user-facing error that never contains a URL or image data."""


def attachment_image_urls(text: str) -> list[str]:
    """Parse QQ attachment descriptions; callers must pass only Reply text."""
    urls: list[str] = []
    blocks = re.split(r"(?m)^[ \t]*\[附件\d+\][ \t]*", text)[1:]
    for block in blocks:
        fields = {}
        for line in block.lstrip("\r\n").splitlines():
            match = re.fullmatch(r"\s*(类型|文件名|URL)\s*[:：]\s*(.*?)\s*", line)
            if not match:
                break
            key, value = match.groups()
            if key in fields:
                break
            fields[key] = value
        if fields.get("类型") == "图片" and fields.get("URL"):
            urls.append(fields["URL"])
    return urls


def _check_public_ip(host: str) -> None:
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        raise ReferenceImageError("图片链接的目标地址无效。") from None
    if (
        not address.is_global
        or address.is_multicast
        or address.is_unspecified
        or address.is_reserved
        or "%" in host
    ):
        raise ReferenceImageError(
            "图片链接指向本地、内网或其他非公网地址，已拒绝下载。"
        )
    if isinstance(address, ipaddress.IPv6Address):
        if address.ipv4_mapped:
            _check_public_ip(str(address.ipv4_mapped))
        # Do not allow IPv4 translation/tunnel addresses to bypass IPv4 checks.
        if (
            address.sixtofour is not None
            or address.teredo is not None
            or address in ipaddress.ip_network("64:ff9b::/96")
            or address in ipaddress.ip_network("64:ff9b:1::/48")
        ):
            raise ReferenceImageError("图片链接使用不支持的网络转换地址，已拒绝下载。")


def _check_url(url: str, allow_any_port: bool = False) -> URL:
    """Validate a remote image URL before any request is made.

    Args:
        url: The candidate image URL.
        allow_any_port: Whether non-standard ports are accepted. Image URLs
            returned by the configured API server may live on its own gateway
            port, so those skip the port allow-list; every other check still
            applies.

    Returns:
        The normalized URL to request.

    Raises:
        ReferenceImageError: The URL is not a public HTTP(S) image address.
    """
    if any(char.isspace() or ord(char) < 32 for char in url) or "\\" in url:
        raise ReferenceImageError("图片链接包含无效字符。")
    try:
        # aiohttp uses yarl, which can normalize Unicode hostnames into IPs.
        # Validate and send the same URL object so normalization cannot bypass
        # the literal-IP checks and the connector's DNS resolver.
        parsed = URL(url)
        host = parsed.raw_host
        port = parsed.port
    except ValueError:
        raise ReferenceImageError("图片链接格式无效。") from None
    if (
        parsed.scheme not in ("http", "https")
        or not host
        or parsed.user is not None
        or parsed.password is not None
        or port is None
        or "%" in host
    ):
        raise ReferenceImageError(
            "图片链接仅支持不含凭据的 HTTP(S) 公网地址及有效端口。"
        )
    # Restrict outbound requests to standard web ports so this reader cannot be
    # used to probe arbitrary services on public hosts.
    if not allow_any_port and port not in ALLOWED_PORTS:
        raise ReferenceImageError("图片链接仅支持 80、443、8080、8443 端口。")
    if host.rstrip(".").lower() == "localhost" or host.lower().endswith(".localhost"):
        raise ReferenceImageError("图片链接指向本地地址，已拒绝下载。")
    # aiohttp 3.11 also skips DNS for shorthand/numeric forms (127.1,
    # 2130706433, trailing dots, etc.). Reject non-canonical IP spellings.
    if ":" in host or host.replace(".", "").isdigit():
        _check_public_ip(host)
    # All other hostnames are checked by the resolver at connection time.
    return parsed


class _PublicResolver(aiohttp.resolver.ThreadedResolver):
    """Validate the exact DNS answers used by the connector, avoiding rebinding."""

    async def resolve(self, host, port=0, family=socket.AF_INET):
        records = await super().resolve(host, port, family)
        if not records:
            raise ReferenceImageError("图片链接的域名未解析到可用地址。")
        for record in records:
            _check_public_ip(record["host"])
        return records


async def download_image(url: str, allow_any_port: bool = False) -> bytes:
    """Download and validate a remote image with strict SSRF and size guards.

    Args:
        url: The image URL to download.
        allow_any_port: Accept an image URL on any public port. This is used for
            URLs returned by the configured image API, whose gateway may not use
            a standard web port.

    Returns:
        The raw image bytes.

    Raises:
        ReferenceImageError: The URL is unsafe, unreachable, oversized or not a
            supported image.
    """
    target = _check_url(url, allow_any_port)
    try:
        # One deadline covers DNS, every redirect and the complete response body.
        async with asyncio.timeout(DOWNLOAD_TIMEOUT):
            resolver = _PublicResolver()
            try:
                connector = aiohttp.TCPConnector(resolver=resolver, use_dns_cache=False)
                async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=aiohttp.ClientTimeout(
                        total=DOWNLOAD_TIMEOUT, sock_connect=5, sock_read=5
                    ),
                    trust_env=False,
                    auto_decompress=False,
                    cookie_jar=aiohttp.DummyCookieJar(),
                    headers={"Accept-Encoding": "identity"},
                ) as session:
                    for redirect in range(MAX_REDIRECTS + 1):
                        async with session.get(
                            target, allow_redirects=False
                        ) as response:
                            if response.status in (301, 302, 303, 307, 308):
                                location = response.headers.get("Location")
                                if not location or redirect == MAX_REDIRECTS:
                                    raise ReferenceImageError(
                                        "图片下载失败：重定向无效或次数过多。"
                                    )
                                target = _check_url(
                                    urljoin(str(target), location),
                                    allow_any_port,
                                )
                                continue
                            if not 200 <= response.status < 300:
                                logger.warning(
                                    "openai_image: reference image download "
                                    "failed with HTTP %s for %s",
                                    response.status,
                                    target,
                                )
                                raise ReferenceImageError(
                                    "图片下载失败，链接可能已过期或无权访问。"
                                )
                            if (
                                response.headers.get(
                                    "Content-Encoding", "identity"
                                ).lower()
                                != "identity"
                            ):
                                raise ReferenceImageError(
                                    "图片下载失败：不支持压缩传输的图片响应。"
                                )
                            if (
                                response.content_length is not None
                                and response.content_length > MAX_IMAGE_BYTES
                            ):
                                raise ReferenceImageError("图片超过 20 MiB 大小限制。")
                            body = bytearray()
                            async for chunk in response.content.iter_chunked(64 * 1024):
                                if len(body) + len(chunk) > MAX_IMAGE_BYTES:
                                    raise ReferenceImageError(
                                        "图片超过 20 MiB 大小限制。"
                                    )
                                body.extend(chunk)
                            return bytes(body)
            finally:
                await resolver.close()
    except ReferenceImageError:
        raise
    except TimeoutError:
        raise ReferenceImageError("图片下载超时，请使用仍可访问的图片。") from None
    except (aiohttp.ClientError, OSError, ValueError):
        raise ReferenceImageError(
            "图片下载失败，链接可能已过期、不可访问或不是安全的公网地址。"
        ) from None
    raise ReferenceImageError("图片下载失败。")


def _validate_image(body: bytes) -> None:
    if not body:
        raise ReferenceImageError("图片内容为空。")
    if len(body) > MAX_IMAGE_BYTES:
        raise ReferenceImageError("图片超过 20 MiB 大小限制。")
    try:
        with PILImage.open(BytesIO(body), formats=SUPPORTED_FORMATS) as image:
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ReferenceImageError("图片超过 4000 万像素限制。")
            image.verify()
        # verify() alone does not decode pixels for every supported format.
        with PILImage.open(BytesIO(body), formats=SUPPORTED_FORMATS) as image:
            image.load()
    except ReferenceImageError:
        raise
    except (PILImage.DecompressionBombError, PILImage.DecompressionBombWarning):
        raise ReferenceImageError("图片像素数量过大，已拒绝读取。") from None
    except Exception:
        raise ReferenceImageError(
            "图片格式不支持或内容已损坏；支持 PNG、JPEG、WebP、GIF、BMP。"
        ) from None


async def read_image(value: str, allow_any_port: bool = False) -> str:
    """Return validated raw base64 from an explicit URL, data URI or base64.

    Args:
        value: A URL, data URI or base64 payload.
        allow_any_port: Accept an explicit URL on any public port. Only image
            URLs returned by the configured API should opt in.

    Returns:
        The validated raw base64 payload.

    Raises:
        ReferenceImageError: The image cannot be read safely.
    """
    value = value.strip()
    if value[:6].lower().startswith(("http:", "https:")):
        body = await download_image(value, allow_any_port)
    else:
        if value.startswith("data:"):
            header, separator, _ = value.partition(",")
            if (
                not separator
                or not header.startswith("data:image/")
                or not header.endswith(";base64")
            ):
                raise ReferenceImageError(
                    "图片 Data URI 必须包含 image 类型及 Base64 数据。"
                )
        _, data, _ = split_image_value(value)
        if len(data) > ((MAX_IMAGE_BYTES + 2) // 3) * 4:
            raise ReferenceImageError("图片超过 20 MiB 大小限制。")
        try:
            body = base64.b64decode(data, validate=True)
        except (binascii.Error, ValueError):
            raise ReferenceImageError("图片不是有效的 Base64 数据。") from None
    await asyncio.to_thread(_validate_image, body)
    return base64.b64encode(body).decode("ascii")


async def read_component_image(component: Image) -> str:
    """Keep AstrBot's component conversion while guarding all remote reads."""
    try:
        source = component.url or component.file or ""
        if source[:6].lower().startswith(("http:", "https:")):
            # AstrBot 4.28's downloader has no size/SSRF controls. Download safely
            # here and skip the component conversion round-trip: read_image
            # already returns validated raw base64.
            return await read_image(source)
        # Preserve local component files, but do not let file:// or UNC paths
        # initiate unchecked SMB/network reads through AstrBot's media resolver.
        # Do not pass large inline payloads to urlsplit's global URL cache.
        if not source.startswith(("base64://", "data:")):
            path = source
            parsed = urlsplit(source) if ":" in source else None
            if parsed is not None and parsed.scheme.lower() == "file":
                if (
                    parsed.netloc
                    and parsed.netloc.lower() != "localhost"
                    and not re.fullmatch(r"[A-Za-z]:", parsed.netloc)
                ):
                    raise ReferenceImageError(
                        "图片组件不支持网络文件地址，请提供 HTTP(S) 公网图片。"
                    )
                path = unquote(parsed.path)
                if re.fullmatch(r"[A-Za-z]:", parsed.netloc or ""):
                    path = f"{parsed.netloc}{path}"
            if path.replace("\\", "/").startswith("//"):
                raise ReferenceImageError(
                    "图片组件不支持网络文件路径，请提供 HTTP(S) 公网图片。"
                )
            # Only files the platform adapter cached under the AstrBot data
            # directory may be read, so the plugin never becomes an arbitrary
            # local file reader.
            try:
                resolved = Path(path).resolve(strict=False)
            except (OSError, ValueError):
                raise ReferenceImageError("图片组件的本地路径无效。") from None
            data_root = Path(get_astrbot_data_path()).resolve(strict=False)
            if not resolved.is_relative_to(data_root):
                raise ReferenceImageError(
                    "图片组件仅支持读取 AstrBot 数据目录内的本地图片。"
                )
        data = await asyncio.wait_for(component.convert_to_base64(), DOWNLOAD_TIMEOUT)
        return await read_image(data)
    except ReferenceImageError:
        raise
    except Exception:
        raise ReferenceImageError(
            "图片组件读取失败，平台可能未提供可访问的图片数据。"
        ) from None
