import asyncio
import sqlite3
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

DB_PATH = os.environ.get("CATALOG_DB", "catalog_full.sqlite")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "<PUT_YOUR_BOT_TOKEN_HERE>")  # set this in environment or config

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def search_by_oem(oem, limit=20):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    q = "SELECT SKU, OEM, Brand, Model, Years, Type, Full_Title, Quantity, Price FROM parts WHERE OEM LIKE ? OR Compatible_OEMs LIKE ? LIMIT ?"
    cur.execute(q, (f"%{oem}%", f"%{oem}%", limit))
    rows = cur.fetchall()
    conn.close()
    return rows

def search_by_text(text, limit=20):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    q = "SELECT SKU, OEM, Brand, Model, Years, Type, Full_Title, Quantity, Price FROM parts WHERE Full_Title LIKE ? OR Original_Name LIKE ? LIMIT ?"
    cur.execute(q, (f"%{text}%", f"%{text}%", limit))
    rows = cur.fetchall()
    conn.close()
    return rows

@dp.message(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer(f"Привет! Это магазин 'Зачпасти у Алёшки'.\nОтправь OEM-номер или название детали для поиска.\nКоманды: /vin - проверить по VIN, /help")

@dp.message(commands=["help"])
async def help_cmd(message: types.Message):
    await message.answer("Отправьте OEM или текст для поиска. /vin - проверить по VIN (отправьте VIN после команды).")

@dp.message(commands=["vin"])
async def vin_cmd(message: types.Message):
    await message.answer("Отправьте VIN (17 символов) для проверки совместимости.")

@dp.message()
async def handle_text(message: types.Message):
    text = message.text.strip()
    if len(text) == 17 and text.isalnum():
        # This is a VIN — decode with public API (vPIC) for basic make/model/year
        import requests
        url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvaluesextended/{text}?format=json"
        try:
            r = requests.get(url, timeout=10).json()
            rec = r.get("Results", [{}])[0]
            make = rec.get("Make") or ""
            model = rec.get("Model") or ""
            year = rec.get("ModelYear") or ""
            resp = f"VIN decoded: {make} {model} {year}\nShowing possible compatible parts (brand/model match)."
            await message.answer(resp)
            rows = []
            if make:
                rows = search_by_text(make)  # simple fallback
            if rows:
                for r in rows[:10]:
                    sku, oem, brand, model, years, ptype, title, qty, price = r
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="Купить", callback_data=f"buy:{sku}")],
                        [InlineKeyboardButton(text="Написать продавцу", callback_data=f"msg:{sku}")]
                    ])
                    text_msg = f"{title}\nOEM: {oem}\nЦена: {price} ₽\nОстаток: {qty}\nSKU: {sku}"
                    await message.answer(text_msg, reply_markup=kb)
            else:
                await message.answer("Совместимых деталей не найдено.")
        except Exception as e:
            await message.answer("Ошибка при декодировании VIN.")
        return
    # else treat as OEM or text search
    rows = search_by_oem(text)
    if not rows:
        rows = search_by_text(text)
    if not rows:
        await message.answer("Ничего не найдено по запросу.")
        return
    for r in rows[:10]:
        sku, oem, brand, model, years, ptype, title, qty, price = r
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Купить", callback_data=f"buy:{sku}"),
             InlineKeyboardButton(text="Написать продавцу", callback_data=f"msg:{sku}")]
        ])
        # Try to find local image
        img_path = None
        possible = f"images/{oem}.jpg"
        if os.path.exists(possible):
            img_path = possible
        if img_path:
            await message.answer_photo(photo=types.InputFile(img_path), caption=f"{title}\nЦена: {price} ₽\nОстаток: {qty}\nSKU: {sku}", reply_markup=kb)
        else:
            await message.answer(f"{title}\nOEM: {oem}\nЦена: {price} ₽\nОстаток: {qty}\nSKU: {sku}", reply_markup=kb)

@dp.callback_query(lambda c: c.data and c.data.startswith("buy:"))
async def process_buy(call: types.CallbackQuery):
    sku = call.data.split(":",1)[1]
    await call.message.answer(f"Вы хотите купить SKU {sku}. Напишите свои контактные данные и адрес доставки, либо нажмите 'Написать продавцу'.")
    await call.answer()

@dp.callback_query(lambda c: c.data and c.data.startswith("msg:"))
async def process_msg(call: types.CallbackQuery):
    sku = call.data.split(":",1)[1]
    await call.message.answer(f"Напишите сообщение по SKU {sku}. Ваше сообщение будет отправлено продавцу.")
    await call.answer()

async def main():
    try:
        print("Starting bot...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
