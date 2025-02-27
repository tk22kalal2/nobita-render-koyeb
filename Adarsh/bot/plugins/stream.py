


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

from pyrogram import Client
from pyrogram.errors import FloodWait


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

        for msg in messages:

            if bool(CUSTOM_CAPTION) & bool(msg.document):
                caption = CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, filename=msg.document.file_name)
            else:
                caption = "" if not msg.caption else msg.caption.html

            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None

            try:
                log_msg = await msg.forward(chat_id=Var.BIN_CHANNEL)
                await asyncio.sleep(0.5)
                stream_link = f"{Var.URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
                online_link = f"{Var.URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
                
                X = await log_msg.reply_text(text=f"{caption} \n**Stream ʟɪɴᴋ :** {stream_link}", disable_web_page_preview=True, quote=True)
                try:
                    await X.forward(chat_id=Var.CB_CHANNEL)
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"Error forwarding message to CB_CHANNEL: {e}")                 
                    await msg.reply_text(
                        text=f"{get_name(log_msg)} \n**Stream ʟɪɴᴋ :** {stream_link}", disable_web_page_preview=True, quote=True
                    )    
            except FloodWait as e:
                print(f"Sleeping for {str(e.x)}s")
                await asyncio.sleep(e.x)
                
@StreamBot.on_message((filters.private) & (filters.document | filters.video | filters.audio | filters.photo), group=4)    
async def private_receive_handler(c: Client, m: Message):
    if bool(CUSTOM_CAPTION) and bool(m.video):
        caption = CUSTOM_CAPTION.format(
            previouscaption="" if not m.caption else m.caption.html,
            filename=m.video.file_name
        )
    else:
        caption = m.caption.html if m.caption else get_name(m.video)

    try:
        log_msg = await m.forward(chat_id=Var.BIN_CHANNEL)
        await asyncio.sleep(0.5)
        stream_link = f"{Var.URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        online_link = f"{Var.URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
                
        X = await log_msg.reply_text(text=f"{caption} \n**Stream ʟɪɴᴋ :** {stream_link}", disable_web_page_preview=True, quote=True)
        try:
            await X.forward(chat_id=Var.CB_CHANNEL)
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Error forwarding message to CB_CHANNEL: {e}")                 
            await msg.reply_text(
                text=f"{get_name(log_msg)} \n**Stream ʟɪɴᴋ :** {stream_link}", disable_web_page_preview=True, quote=True
            )    
    except FloodWait as e:
        print(f"Sleeping for {str(e.x)}s")
        await asyncio.sleep(e.x)        
                            
@StreamBot.on_message(filters.channel & ~filters.group & (filters.document | filters.video | filters.photo)  & ~filters.forwarded, group=-1)
async def channel_receive_handler(bot, broadcast):
    if MY_PASS:
        check_pass = await pass_db.get_user_pass(broadcast.chat.id)
        if check_pass == None:
            await broadcast.reply_text("Login first using /login cmd \n don\'t know the pass? request it from developer!")
            return
        if check_pass != MY_PASS:
            await broadcast.reply_text("Wrong password, login again")
            await pass_db.delete_user(broadcast.chat.id)
            
            return
    if int(broadcast.chat.id) in Var.BANNED_CHANNELS:
        await bot.leave_chat(broadcast.chat.id)
        
        return
    try:
        log_msg = await broadcast.forward(chat_id=Var.BIN_CHANNEL)
        stream_link = f"{Var.URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        online_link = f"{Var.URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        await log_msg.reply_text(
            text=f"**Channel Name:** `{broadcast.chat.title}`\n**CHANNEL ID:** `{broadcast.chat.id}`\n**ʀᴇǫᴜᴇꜱᴛ ᴜʀʟ:** {stream_link}",
            quote=True
        )
        await bot.edit_message_reply_markup(
            chat_id=broadcast.chat.id,
            message_id=broadcast.id,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🖥️  ꜱᴛʀᴇᴀᴍ  🖥️", url=stream_link),
                     InlineKeyboardButton('📥  ᴅᴏᴡɴʟᴏᴀᴅ  📥', url=online_link)],
                    [InlineKeyboardButton('🎪  ꜱᴜʙꜱᴄʀɪʙᴇ ᴍʏ ʏᴛ ᴄʜᴀɴɴᴇʟ  🎪', url='https://youtube.com/@NobiDeveloper')]
                ]
            )
        )
    except FloodWait as w:
        print(f"Sleeping for {str(w.x)}s")
        await asyncio.sleep(w.x)
        await bot.send_message(chat_id=Var.BIN_CHANNEL,
                             text=f"GOT FLOODWAIT OF {str(w.x)}s FROM {broadcast.chat.title}\n\n**CHANNEL ID:** `{str(broadcast.chat.id)}`",
                             disable_web_page_preview=True)
    except Exception as e:
        await bot.send_message(chat_id=Var.BIN_CHANNEL, text=f"**#ERROR_TRACKEBACK:** `{e}`", disable_web_page_preview=True)
        print(f"Cᴀɴ'ᴛ Eᴅɪᴛ Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ!\nEʀʀᴏʀ:  **Give me edit permission in updates and bin Channel!{e}**")

#batch2 command


        
