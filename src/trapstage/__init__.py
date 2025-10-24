from mwbot import Bot, arktool


async def main(page: str, username: str, password: str) -> None:
    bot = Bot(
        sitename="PRTS",
        api="https://prts.wiki/api.php",
        index="https://prts.wiki/index.php",
        username=username,
        password=password,
    )
    print(len(username), len(password))

    await bot.login()

    arktool.read_ark_file("excel/skill_table.json")
