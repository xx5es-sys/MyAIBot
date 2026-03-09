import asyncio
import time
from premium_util import is_premium, consume_for_single, refund_credit, update_last_chk

API_TOKEN = '7830034663:AAHcEFO9dHuQRPdRx93sKwYt2TzWGBvev70'
auth_chats = {'private': [6131333309], 'group': [-1002773091911]}
Admin = 6131333309
PAYMENT_PROVIDER_TOKEN = ""

last_use = {}

async def can_use_b3(chat_id, user_id):
    """
    Check if user can use single check command.
    For Premium/Unlimited: consume credit before execution.
    For Free users in auth_chats: apply 30-second cooldown.
    """
    current_time = time.time()
    user_id_str = str(user_id)
    
    # Admin always allowed
    if user_id == Admin:
        return True
    
    # Check if premium (unlimited or credits>0)
    if await is_premium(user_id_str):
        # Try to consume credit
        success, msg = await consume_for_single(user_id_str)
        if success:
            return True
        else:
            # No credits available
            return False
    
    # Free users in authorized chats
    if chat_id in auth_chats['private']:
        return True
    elif chat_id in auth_chats['group']:
        key = (chat_id, user_id)
        if key in last_use and current_time - last_use[key] < 30:
            return False
        last_use[key] = current_time
        return True
    
    return False
