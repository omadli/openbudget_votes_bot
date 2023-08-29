import io
import base64
import json
from aiohttp import ClientSession

from config import INITIATIVE_ID

CAPTCHA_URL = "https://openbudget.uz/api/v2/vote/captcha-2"
GET_INITIATIVE_TOKEN_URL = "https://openbudget.uz/api/v2/info/get-initiative-token"
VOTES_URL = "https://openbudget.uz/api/v2/info/votes/"

HEADERS1 = {
    "authority": "openbudget.uz",
    "method": "GET",
    "path": "/api/v2/vote/captcha-2",
    "scheme": "https",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9,uz;q=0.8,ru;q=0.7",
    "Access-Captcha": "cy0xMmU4NGs3MnI0OGUxMXQ=",
    "Authorization": "",
    "Cookie": "route=8dade84b05a3eb3941951e352cf157e5",
    "Dnt": "1",
    "Referer": f"https://openbudget.uz/boards/initiatives/initiative/31/{INITIATIVE_ID}",
    "Sec-Ch-Ua": "\"Chromium\";v=\"116\", \"Not)A;Brand\";v=\"24\", \"Google Chrome\";v=\"116\"",  # noqa: E501
    "Sec-Ch-Ua-Mobile": "?1",
    "Sec-Ch-Ua-Platform": "Android",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"  # noqa: E501
}

HEADERS2 = {
    "authority": "openbudget.uz",
    "method": "POST",
    "path": "/api/v2/info/get-initiative-token",
    "scheme": "https",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9,uz;q=0.8,ru;q=0.7",
    "Authorization": "",
    "Content-Length": 116,
    "Content-Type": "application/json",
    "Cookie": "route=8dade84b05a3eb3941951e352cf157e5",
    "Dnt": "1",
    "Origin": "https://openbudget.uz",
    "Referer": f"https://openbudget.uz/boards/initiatives/initiative/31/{INITIATIVE_ID}",
    "Sec-Ch-Ua": "\"Chromium\";v=\"116\", \"Not)A;Brand\";v=\"24\", \"Google Chrome\";v=\"116\"",  # noqa: E501
    "Sec-Ch-Ua-Mobile": "?1",
    "Sec-Ch-Ua-Platform": "Android",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"  # noqa: E501
}

HEADERS3 = {
    "authority": "openbudget.uz",
    "method": "GET",
    "scheme": "https",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9,uz;q=0.8,ru;q=0.7",
    "Access-Captcha": "cy0xMmU4NGs3MnI0OGUxMXQ=",
    "Authorization": "",
    "Dnt": "1",
    "Referer": f"https://openbudget.uz/boards/initiatives/initiative/31/{INITIATIVE_ID}",
    "Sec-Ch-Ua": "\"Chromium\";v=\"116\", \"Not)A;Brand\";v=\"24\", \"Google Chrome\";v=\"116\"",  # noqa: E501
    "Sec-Ch-Ua-Mobile": "?1",
    "Sec-Ch-Ua-Platform": "Android",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"  # noqa: E501
}


async def get_captcha(session: ClientSession) -> (io.BytesIO, str):
    async with session.get(CAPTCHA_URL, headers=HEADERS1) as resp:
        if resp.status != 200:
            raise Exception(str(resp.status) + await resp.text())
        json_resp = await resp.json()
        base64_image = json_resp["image"]
        base64_image = base64_image[:100] + base64_image[132:]
        captcha_key = json_resp["captchaKey"]
        img = io.BytesIO(base64.b64decode(base64_image))
        img.seek(0)
        return (img, captcha_key)
    


async def check_captcha(session: ClientSession, captcha_key: str, captcha_result: str) -> str:  # noqa: E501
    captcha_result = str(captcha_result)
    params = {"captchaKey": captcha_key, "captchaResult": captcha_result, "initiativeId": INITIATIVE_ID}  # noqa: E501
    request_data = json.dumps(params)
    HEADERS2.update({"Content-Length": str(len(request_data))})
    async with session.post(GET_INITIATIVE_TOKEN_URL, data=request_data, headers=HEADERS2) as resp:  # noqa: E501
        if resp.status != 200:
            raise Exception(str(resp.status) + await resp.text())
        json_resp = await  resp.json()
        token = json_resp["token"]
        return token



async def get_list_votes(session: ClientSession, token: str, page: int=0) -> (int, list):  # noqa: E501
    async with session.get(VOTES_URL + token + f"?page={str(page)}", timeout=5) as resp:
        if resp.status != 200:
            raise Exception(str(resp.status) + await resp.text())
        resp_json = await resp.json()
        total_pages = resp_json["totalPages"]
        result = resp_json['content']
        return total_pages, result
