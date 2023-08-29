import io
import json
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.storage import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiohttp import ClientSession

from config import API_TOKEN
from api import get_captcha, check_captcha, get_list_votes

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot=bot, storage=MemoryStorage())
session = None


async def on_startup(dp: Dispatcher):
    await bot.set_my_commands(
        commands=[
            types.BotCommand("start", "Botni ishga tushirish"),
            types.BotCommand("get", "Ovozlar ro'yxatini yuklab olish"),
        ]
    )


@dp.message_handler(commands="start", state='*')
async def cmd_start(msg: types.Message, state: FSMContext):
    await msg.answer(f"Assalomu alaykum {msg.from_user.get_mention(as_html=True)}")
    if state is not None:
        await state.finish()


@dp.message_handler(commands="get")
async def cmd_get(msg: types.Message, state: FSMContext):
    global session
    session = ClientSession()
    try:
        image, captcha_key = await get_captcha(session)
        await msg.answer_photo(image, caption="Captcha javobini kiriting:")
        await state.set_state("captcha")
        await state.set_data({"captcha_key": captcha_key})
    except Exception as e:
        await msg.answer(e)
        if state is not None:
            await state.finish()


@dp.message_handler(state="captcha")
async def captcha_handler(msg: types.Message, state: FSMContext):
    if not msg.text.isnumeric():
        await msg.answer("Iltimos to'g'ri javob kiriting yoki boshqatdan urinib ko'ring. /start")  # noqa: E501
    global session
    try:
        data = await state.get_data()
        captcha_key = data["captcha_key"]
        token = await check_captcha(session, captcha_key, msg.text)
        await msg.answer(
            text=f"Token: <code>{token}</code>\nBarcha ovozlar ro'yxati yuklab olinsinmi?",  # noqa: E501
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="✅Yuklash", callback_data="dl")],
                    [types.InlineKeyboardButton(text="❌Shart emas", callback_data="cancel")]  # noqa: E501
                ]
            )
        )
        await state.set_state("download")
        await state.set_data({"token": token})
    except Exception as e:
        await msg.answer(e)
        if state is not None:
            await state.finish()


@dp.callback_query_handler(text="dl", state="download")
async def dl_handler(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.delete()
    data = await state.get_data()
    token = data["token"]
    global session
    try:
        total_pages, content = await get_list_votes(session, token)
        await call.message.answer(
            f"Yuklab olinmoqda...\n"
            f"Jami {total_pages+1} sahifa"
        )
        await call.message.answer_chat_action(
            action=types.ChatActions.UPLOAD_DOCUMENT
        )
        for page in range(1, total_pages):
            _, content1 = await get_list_votes(session, token, page)
            content += content1
        
        count_votes = len(content)
        json_data = json.dumps(content, indent=4)
        doc = io.BytesIO(json_data.encode())
        doc.seek(0)
        await call.message.answer_document(
            document=types.InputFile(doc, "votes.json"),
            caption=f"Jami {count_votes} ta ovoz"
        )
        await state.finish()
    except Exception as e:
        await call.message.answer(e)
        if state is not None:
            await state.finish()


@dp.callback_query_handler(text="cancel", state="download")
async def cancel_dl_handler(call: types.CallbackQuery, state: FSMContext):
    await call.answer("Bekor qilindi")
    await call.message.delete()
    await call.message.answer("Bekor qilindi.")
    await state.finish()


@dp.message_handler(state="download")
async def dl_msg_handler(msg: types.Message, state: FSMContext):
    await msg.answer(
        "Tepadagi tugmalardan foydalaning yoki /start bosing."
    )

if __name__ == '__main__':
    executor.start_polling(
        dispatcher=dp,
        skip_updates=True,
        on_startup=on_startup
    )   
