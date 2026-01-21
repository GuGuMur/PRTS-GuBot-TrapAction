from mwbot import Bot, utils
from pathlib import Path  # noqa: F401
import asyncio
from trapstage.source.local import return_text as rtl
import re
import json

patterns = [r"装置\s*==", r"==\s*区块"]


async def deal(title, sem: asyncio.Semaphore):
    async with sem:
        text = await bot.get_page_text(title=title)
        for i in patterns:
            if re.search(i, text):
                return
        if "{{敌方情报" not in text:
            return
        text2 = await rtl(
            pagetext=text,
            unedittrap=False,
            unwritetiles1=unwritetiles,
            tilesformat1=tilesformat,
            unwritetraps1=unwritetraps,
            trapsformat1=trapsformat,
        )
        # print(text2["text"])
        if text2["status"]:
            # text2 = text2["text"]
            # if text != text2:
            # print(text2)
            await bot.edit_page(
                title=title, text=text2["text"], summary="//Edit by TrapperScriptBot."
            )


async def main(page: str, username: str, password: str) -> None:
    global bot
    bot = Bot(
        sitename="PRTS",
        api="https://prts.wiki/api.php",
        index="https://prts.wiki/index.php",
        username=username,
        password=password,
    )
    await bot.login()
    global unwritetiles, tilesformat, trapsformat, unwritetraps
    unwritetiles = await bot.get_page_text("特殊地形/trapper/unwritetiles.json")
    unwritetiles = json.loads(unwritetiles)
    tilesformat = await bot.get_page_text("特殊地形/trapper/tilesformat.json")
    tilesformat = json.loads(tilesformat)
    unwritetraps = await bot.get_page_text("模板:关卡装置/trapper/unwritetraps.json")
    unwritetraps = json.loads(unwritetraps)
    trapsformat = await bot.get_page_text("模板:关卡装置/trapper/trapsformat.json")
    trapsformat = json.loads(trapsformat)
    # trapsformat = json.loads( Path("./full.json").read_text(encoding="utf-8") )
    new_pages = await bot.get_page_text(page)

    pagelist_ori = utils.get_all_links(new_pages)
    pagelist = sorted(list(set(pagelist_ori)), key=pagelist_ori.index)
    tasks = []
    sem = asyncio.Semaphore(10)
    for i in pagelist:
        tasks.append(deal(i, sem))
    await asyncio.gather(*tasks)
    # for i in pagelist:
    #     text = await bot.get_page_text(title=i)
    #     a = await rtl(pagetext=text, unedittrap=False)
    #     a = a["text"]
    #     print(a)
    # if a != text:
    #     await bot.edit_page(title=i, text=a, summary="//Edit by TrapperScript-Local")

async def test(page: str, username: str, password: str) -> None:
    bot = Bot(
        sitename="PRTS",
        api="https://prts.wiki/api.php",
        index="https://prts.wiki/index.php",
        username=username,
        password=password,
    )
    await bot.login()
    global unwritetiles, tilesformat, trapsformat, unwritetraps
    unwritetiles = await bot.get_page_text("特殊地形/trapper/unwritetiles.json")
    unwritetiles = json.loads(unwritetiles)
    tilesformat = await bot.get_page_text("特殊地形/trapper/tilesformat.json")
    tilesformat = json.loads(tilesformat)
    unwritetraps = await bot.get_page_text("模板:关卡装置/trapper/unwritetraps.json")
    unwritetraps = json.loads(unwritetraps)
    trapsformat = await bot.get_page_text("模板:关卡装置/trapper/trapsformat.json")
    trapsformat = json.loads(trapsformat)
    # trapsformat = json.loads( Path("./full.json").read_text(encoding="utf-8") )
    text = await bot.get_page_text(title=page)
    a = await rtl(
        pagetext=text,
        unedittrap=False,
        unwritetiles1=unwritetiles,
        tilesformat1=tilesformat,
        unwritetraps1=unwritetraps,
        trapsformat1=trapsformat,
    )
    print(json.dumps(a, ensure_ascii=False, indent=4))

if __name__ == "__main__":
    asyncio.run(main())
