from mwbot import Bot

async def main(username: str, password: str) -> None:
    bot = Bot(
        sitename="PRTS",
        api="https://prts.wiki/api.php",
        index="https://prts.wiki/index.php",
        username=username,
        password=password,
    )
    await bot.login()
