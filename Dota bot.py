import asyncio
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.filters.command import CommandObject
IGNORE_ITEMS = {
    "Town Portal Scroll",
    "Observer Ward",
    "Sentry Ward",
    "Smoke of Deceit",
    "Magic Stick",
    "Magic Wand",
    "Boots of Speed"
}

TOKEN = "7772428572:AAHLaj5SmKloNDiXwS2qnkFrqcBoBetJf7o"

def format_items(stage_data, items_by_id, limit=4):
    if not isinstance(stage_data, dict):
        return []

    sorted_items = sorted(
        stage_data.items(),
        key=lambda x: x[1],
        reverse=True
    )

    result = []
    for item_id, _ in sorted_items:
        name = items_by_id.get(int(item_id))
        if not name or name in IGNORE_ITEMS:
            continue

        result.append(name)
        if len(result) == limit:
            break

    return result
async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    @dp.message(Command("meta"))
    async def meta_handler(message: Message):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.opendota.com/api/heroStats") as resp:
                heroes = await resp.json()

        heroes = [
            h for h in heroes
            if h["pro_pick"] > 100
        ]

        top = sorted(
            heroes,
            key=lambda h: (h["pro_win"] / h["pro_pick"]),
            reverse=True
        )[:5]

        text = " Мета герои (Pro сцена):\n\n"

        for h in top:
            winrate = h["pro_win"] / h["pro_pick"] * 100
            text += f" {h['localized_name']} — {winrate:.1f}% WR\n"

        await message.answer(text)

    @dp.message(Command("hero"))
    async def hero_handler(message: Message, command: CommandObject):
        hero_name = command.args

        if not hero_name:
            await message.answer("Напиши: /hero и имя персонажа")
            return

        hero_name = hero_name.lower().strip()

        try:
            async with aiohttp.ClientSession() as session:

                async with session.get("https://api.opendota.com/api/heroes") as resp:
                    heroes = await resp.json()

                hero = next(
                    (
                        h for h in heroes
                        if h["localized_name"].lower() == hero_name
                        or h["name"].replace("npc_dota_hero_", "") == hero_name
                    ),
                    None
                )

                if not hero:
                    await message.answer(" Герой не найден")
                    return

                hero_id = hero["id"]

                async with session.get(
                    f"https://api.opendota.com/api/heroes/{hero_id}/itemPopularity"
                ) as resp:
                    items_popularity = await resp.json()

                core_items = []
                stage = items_popularity.get("mid_game_items") or items_popularity.get("late_game_items")

                core_items = sorted(
                    stage.items(),
                    key=lambda x: x[1],
                    reverse=True
                )

                stage = (
                        items_popularity.get("mid_game_items")
                        or items_popularity.get("late_game_items")
                        or items_popularity.get("early_game_items")
                )

                if not stage:
                    await message.answer(" Нет данных по предметам")
                    return

                core_items = sorted(
                    stage.items(),
                    key=lambda x: x[1],
                    reverse=True
                )

                async with session.get(
                    "https://api.opendota.com/api/constants/items"
                ) as resp:
                    items_data = await resp.json()
                    items_by_id = {}

                    for item in items_data.values():
                        item_id = item.get("id")
                        name = item.get("dname")
                        if item_id and name:
                            items_by_id[item_id] = name
                            early_items = format_items(
                                items_popularity.get("early_game_items"),
                                items_by_id
                            )

                            mid_items = format_items(
                                items_popularity.get("mid_game_items"),
                                items_by_id
                            )

                            late_items = format_items(
                                items_popularity.get("late_game_items"),
                                items_by_id
                            )

                text = f" {hero['localized_name']}\n\n"

                if early_items:
                    text += " Early:\n"
                    for item in early_items:
                        text += f"• {item}\n"
                    text += "\n"

                if mid_items:
                    text += " Mid:\n"
                    for item in mid_items:
                        text += f"• {item}\n"
                    text += "\n"

                if late_items:
                    text += " Late:\n"
                    for item in late_items:
                        text += f"• {item}\n"

                await message.answer(text)

        except Exception as e:
            print("ОШИБКА:", e)
            await message.answer("⚠️ Произошла ошибка")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())








