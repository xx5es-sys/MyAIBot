from aiogram import types, Bot
import aiohttp
from config import auth_chats, can_use_b3
from branding import apply_branding

async def proxycheck(message: types.Message):
    proxy_status = "Dead ❌"
    proxy_encrypted = "Error in Proxy"
    chat_id = message.chat.id
    user_id = message.from_user.id
    bot = message.bot
    message_id_to_edit = None
    
    # Check permission
    if not await can_use_b3(chat_id, user_id):
        await message.reply(apply_branding("Please wait 30 seconds before using this command again."), parse_mode="HTML")
        return
        
    await bot.send_chat_action(chat_id, "typing")
    response_message = await message.reply(apply_branding("wait a moment..."), parse_mode="HTML")
    message_id_to_edit = response_message.message_id
    
    proxy_url = "http://p.webshare.io:80/"
    proxy_auth = aiohttp.BasicAuth('jelxyqtc-rotate', 'vxigi2vt6v8x')
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://httpbin.org/ip", proxy=proxy_url, proxy_auth=proxy_auth, timeout=10) as response:
                if response.status == 200:
                    json_response = await response.json()
                    proxy = json_response["origin"]
                    proxy_status = "Live ✅"
                    proxy_encrypted = proxy[:-6] + "******"
                else:
                    proxy_encrypted = "Error in Proxy"
        except Exception:
            proxy_encrypted = "Error in Proxy"
            
    if message_id_to_edit:
        reply_message = apply_branding(f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝗣𝗿𝗼𝘅𝘆 ⌁ <code>{proxy_encrypted}</code> {proxy_status}")
        await bot.edit_message_text(text=reply_message, chat_id=chat_id, message_id=message_id_to_edit, parse_mode="HTML")
