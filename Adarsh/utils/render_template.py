from Adarsh.vars import Var
from Adarsh.bot import StreamBot
from Adarsh.utils.human_readable import humanbytes
from Adarsh.utils.file_properties import get_file_ids
from Adarsh.server.exceptions import InvalidHash
import urllib.parse
import aiofiles
import logging
import aiohttp


async def render_page(id, secure_hash):
    file_data = await get_file_ids(StreamBot, int(Var.BIN_CHANNEL), int(id))
    if file_data.unique_id[:6] != secure_hash:
        logging.debug(f'link hash: {secure_hash} - {file_data.unique_id[:6]}')
        logging.debug(f"Invalid hash for message with - ID {id}")
        raise InvalidHash
    src = urllib.parse.urljoin(Var.URL, f'{secure_hash}{str(id)}')
    
    if str(file_data.mime_type.split('/')[0].strip()) == 'video':
        async with aiofiles.open('Adarsh/template/req.html') as r:
            heading = 'Watch {}'.format(file_data.file_name)
            tag = file_data.mime_type.split('/')[0].strip()
            html = (await r.read()).replace('tag', tag) % (heading, file_data.file_name, src)
    elif str(file_data.mime_type.split('/')[0].strip()) == 'audio':
        async with aiofiles.open('Adarsh/template/req.html') as r:
            heading = 'Listen {}'.format(file_data.file_name)
            tag = file_data.mime_type.split('/')[0].strip()
            html = (await r.read()).replace('tag', tag) % (heading, file_data.file_name, src)
    else:
        async with aiofiles.open('Adarsh/template/dl.html') as r:
            async with aiohttp.ClientSession() as s:
                async with s.get(src) as u:
                    heading = 'Download {}'.format(file_data.file_name)
                    file_size = humanbytes(int(u.headers.get('Content-Length')))
                    html = (await r.read()) % (heading, file_data.file_name, src, file_size)
    current_url = f'{Var.URL}/{str(id)}/{file_data.file_name}?hash={secure_hash}'
   
    html_code = f'''
    <p>
    <center>
        <button id="downloadBtn" style="border: 0; padding: 0; width: 320px; height: 40px; font-size: 20px; background-color: #2ecc71; border-radius: 5px; color: white;" onclick="window.location.href = '{current_url}'">
            Download Now
        </button>
        <div id="timer" style="margin-top: 10px; font-size: 18px; color: #555;"></div>
    </center>
    </p>
    
    <footer style="position: fixed; left: 0; bottom: 0; width: 100%; background-color: #1b1b1b; color: #ccc; text-align: center; padding: 10px; font-size: 14px;">
    Copyright © 2025 NEXTPULSE.<br>
    All Rights Reserved.
    </footer>
    
    <script>
        let timeLeft = 20;
        const timerEl = document.getElementById("timer");
    
        const countdown = setInterval(() => {
            if (timeLeft >= 0) {{
                timerEl.textContent = "Download will start in " + timeLeft + " second" + (timeLeft !== 1 ? "s" : "") + "...";
                timeLeft--;
            }} else {{
                clearInterval(countdown);
                timerEl.textContent = "Download is ready!";
            }}
        }, 1000);
    </script>
    '''

    html += html_code    
    return html
