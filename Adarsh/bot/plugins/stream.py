import os
from os import getenv, environ
from dotenv import load_dotenv


#(c) NobiDeveloper
import os
import asyncio
from asyncio import TimeoutError
from Adarsh.bot import StreamBot
from Adarsh.utils.database import Database
from Adarsh.utils.human_readable import humanbytes
from Adarsh.vars import Var
from urllib.parse import quote_plus
from pyrogram import filters, Client
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from telethon.tl.types import InputPeerChannel
from Adarsh.utils.file_properties import get_name, get_hash, get_media_file_size
db = Database(Var.DATABASE_URL, Var.name)
from helper_func import encode, get_message_id, decode, get_messages

CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)
#set True if you want to prevent users from forwarding files from bot
PROTECT_CONTENT = True if os.environ.get('PROTECT_CONTENT', "False") == "True" else False

#Set true if you want Disable your Channel Posts Share button
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", None) == 'True'

MY_PASS = os.environ.get("MY_PASS", None)
pass_dict = {}
pass_db = Database(Var.DATABASE_URL, "ag_passwords")

DB_CHANNEL = int(getenv('DB_CHANNEL', ''))

async def get_chat_members_list(self, chat_id):
    try:
        members = await self.get_chat_members(chat_id)
        return members
    except Exception as e:
        print(f"Error fetching chat members: {e}")
        return []
        
@StreamBot.on_message(filters.private & filters.user(list(Var.OWNER_ID)) & filters.command('batch'))
async def batch(client: Client, message: Message):
    while True:
        try:
            # Prompt the user to provide the first message from the DB Channel
            first_message = await client.ask(
                text="Forward the First Message from DB Channel (with Quotes)..\n\nor Send the DB Channel Post Link",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except:
            return  # Return if there's an exception (e.g., timeout)

        # Get the message ID from the provided message or link
        f_msg_id = await get_message_id(client, first_message)

        if f_msg_id:
            break
        else:
            # Inform the user of an error if the message/link is not from the DB Channel
            await first_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is taken from DB Channel", quote=True)
            continue

    while True:
        try:
            # Prompt the user to provide the last message from the DB Channel
            second_message = await client.ask(
                text="Forward the Last Message from DB Channel (with Quotes)..\nor Send the DB Channel Post link",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except:
            return  # Return if there's an exception (e.g., timeout)

        # Get the message ID from the provided message or link
        s_msg_id = await get_message_id(client, second_message)

        if s_msg_id:
            break
        else:
            # Inform the user of an error if the message/link is not from the DB Channel
            await second_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is taken from DB Channel", quote=True)
            continue

    # Generate a list of links for each message between the first and second message
    message_links = []
    for msg_id in range(min(f_msg_id, s_msg_id), max(f_msg_id, s_msg_id) + 1):
        string = f"get-{msg_id * abs(client.db_channel)}"
        base64_string = await encode(string)
        link = f"https://t.me/{client.username}?start={base64_string}"
        message_links.append(link)

    for link in message_links:
        try:
            base64_string = link.split("=", 1)[1]
            decoded_string = await decode(base64_string)
        except Exception as e:
            print(f"Error decoding link: {e}")
            return

        argument = decoded_string.split("-")
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel))
                end = int(int(argument[2]) / abs(client.db_channel))
            except:
                return
            if start <= end:
                ids = range(start, end + 1)
            else:
                ids = []
                i = start
                while True:
                    ids.append(i)
                    i -= 1
                    if i < end:
                        break
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel))]
            except:
                return

        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            print(f"Error fetching messages: {e}")
            await message.reply_text("Something went wrong..!")
            return        

        snt_msgs = []

        for msg in messages:

            if bool(CUSTOM_CAPTION) & bool(msg.document):
                caption = CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, filename=msg.document.file_name)
            else:
                caption = "" if not msg.caption else msg.caption.html

            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None

            import asyncio

       
            try:
                channel_info = await client.get_chat(DB_CHANNEL)
                members_list = await client.get_chat_members_list(channel_info.id)
                for member in members_list:
                    # Send messages to individual members here
                    try:
                        if member.user:
                            await client.send_message(
                                chat_id=member.user.id,
                                text=msg.text,
                                caption=caption,
                                parse_mode=ParseMode.HTML,
                                reply_markup=reply_markup
                            )
                    except Exception as e:
                        print(f"Error sending message to channel member: {e}")
            except Exception as e:
                print(f"Error sending message to channel members: {e}")
 




    

    









