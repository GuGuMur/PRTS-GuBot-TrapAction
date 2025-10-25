import asyncio
import os
import re
import zipfile
from io import BytesIO
from pathlib import Path
from typing import cast

import mwparserfromhell
import ujson as json
import UnityPy
from httpx import AsyncClient
from loguru import logger
from mwbot import Bot, arktool
from mwparserfromhell import parse
from mwparserfromhell.wikicode import Template
from torappu.core import export_client as exporter
from torappu.core.task.task import Client
from torappu.core.task.utils import build_container_path, read_obj
from torappu.models import Version
from UnityPy import Environment
from UnityPy.classes import MonoBehaviour, PPtr
from UnityPy.classes.generated import ComponentPair

from trapedit.static import (
    ASSET_SOURCE,
    HOTUPDATE_LIST,
    PATH,
    VERSION_SOURCE,
)

class RichTextStyles:
    richTextStyles_t = {}
    termDescriptionDict_t = {}
    richTextStyles = {}
    termDescriptionDict = {}

    def __init__(self, gamedata_const):
        self.richTextStyles_t = gamedata_const["richTextStyles"]
        self.termDescriptionDict_t = gamedata_const["termDescriptionDict"]
        for s in self.richTextStyles_t:
            temp = self.richTextStyles_t[s]
            if temp.find("</color>") != -1:
                self.richTextStyles[s] = temp.replace("<color=", "{{color|").replace(
                    ">{0}</color>", "|"
                )
        for k in self.termDescriptionDict_t:
            temp2 = self.termDescriptionDict_t[k]
            self.termDescriptionDict[k] = "{{术语|" + temp2["termId"] + "|"

    def tran1(self, matched):
        code = matched.group(1)
        if code.lower() in self.richTextStyles:
            return self.richTextStyles[code.lower()]
        elif code in self.termDescriptionDict:
            return self.termDescriptionDict[code]
        else:
            return "{{"

    def tran2(self, matched):
        code = matched.group(1)
        if code in self.termDescriptionDict:
            return self.termDescriptionDict[code]
        else:
            return "{{"

    def compile(self, s):
        pattern = re.compile(r"<+@([^>]*)>")
        t = re.sub(pattern, self.tran1, s)
        pattern = re.compile(r"<+\$([^>]*)>")
        t = re.sub(pattern, self.tran2, t)
        t = t.replace("</>", "}}")
        t = t.replace("\\n", "<br>")
        return t


class BBKeyReplace:
    blackboard = {}
    fit = {"": "{:n}", "0%": "{:.0%}", "0.0%": "{:.1%}"}

    def trans(self, matched):
        for term in self.blackboard:
            if term["key"] == matched.group(1):
                return self.fit[matched.group(2)].format(term["value"])
        return "0"

    def compile(self, s, BB):
        self.blackboard = BB
        return re.sub(r"{([^{}:]+):?([^{}]*)}", self.trans, s)


# def GetZipFile(URL, path):
#     resp = urlopen(URL)
#     folder = zipfile.ZipFile(BytesIO(resp.read()))
#     return UnityPy.load(folder.open(path))


async def get_unity_env(version: str, path_list: list[str]):
    # asset_env = UnityPy.load
    assets = []
    for path in path_list:
        bin_data = await asyncFetchData(ASSET_SOURCE(version, path))
        folder = zipfile.ZipFile(BytesIO(bin_data))
        assets.append(folder.open(path))
    # asset_env.load_files(results)
    return UnityPy.load(*assets)


def to_string(value):
    if isinstance(value, bool):
        return "有" if value else "无"
    if isinstance(value, str):
        return rich_text.compile(value)
    return str(value)


def char_data_fill(text, path, data):
    result = {}
    for key, value in path.items():
        if type(value) is str:
            if key in data.keys() and data[key] is not None:
                result[value] = to_string(data[key])
        else:
            result.update(char_data_fill(text, value, data[key]))
    return {k: str(v) for k, v in result.items()}


async def asset_data_fill(asset_data, id, client):
    SCRIPT_SET = {
        "Trap",
        "MapDependentTrap",
        "BossHudTrap",
        "SandboxResTrap",
        "GiantTrap",
    }
    CATEGORY = {1: "默认", 2: "装置", 4: "障碍物"}
    SIDE = {0: "无阵营", 1: "我方", 2: "敌方", 4: "中立"}
    OPTION = {0: "否", 1: "是"}
    CARD_POLICY = {0: "默认", 1: "唯一", 2: "队列"}
    DEPLOY = {0: "无", 1: "部署于近战位", 2: "部署于远程位", 3: "部署于近战/远程位"}
    WITHDRAW = {0: "不可撤回", 1: "不可撤回", 2: "部署后可撤回", 3: "始终可撤回"}

    ab_list = {
        bundle
        for asset, bundle in client.asset_to_bundle.items()
        if asset.startswith("battle/prefabs/[uc]tokens/%s" % (id))
        # if asset.startswith("pkgrps/btl_pfb_tokens_i%s" % (id))
    }
    paths = await client.resolves(list(ab_list))
    ab_path = paths[0][1]
    env = UnityPy.load(ab_path)
    await load_anon(client, env)
    container_map = build_container_path(env)

    objs = list(filter(lambda obj: obj.type.name == "MonoBehaviour", env.objects))
    # print(asset.container)
    dyn_path = f"dyn/battle/prefabs/[uc]tokens/{id}.prefab"
    unanon_assets = cast(
        "list[ComponentPair[PPtr[MonoBehaviour]]]",
        asset_data.container[dyn_path].read().m_Component,
    )
    for pptr in unanon_assets:
        pptr_mono_behaviour = pptr.component.deref_parse_as_object()
        objs.append(pptr_mono_behaviour.object_reader)
    result = {}
    for obj in objs:
        # 先筛类型
        if (data := read_obj(MonoBehaviour, obj)) is None:
            continue
        if not data.m_Script:
            continue
        try:
            class_name = data.m_Script.read().m_ClassName
        except Exception:
            continue
        if class_name not in SCRIPT_SET:
            continue
        # 再筛装置名
        path = (
            container_map[obj.path_id]
            .replace("dyn/battle/prefabs/[uc]tokens/", "")
            .replace(".prefab", "")
        )
        if path != id:
            continue
        # workwork
        tree = obj.read_typetree()
        result["实体类型"] = CATEGORY[tree["_category"]]
        result["阵营"] = SIDE[tree["_sideType"]]
        result["阻挡半径"] = "{:.4f}".format(tree["_blockRadiusSquare"] ** 0.5)
        result["重写地块"] = OPTION[tree["_rewriteTileOptions"]]
        result["再部署策略"] = CARD_POLICY[tree["_cardPolicy"]]
        result["占用部署数"] = tree["_occupiedRemainingCharacterCnt"]
        result["部署条件"] = DEPLOY[tree["_buildCondition"]["buildableType"]]
        result["撤回策略"] = WITHDRAW[
            (tree["_withdrawable"] << 1) + tree["_ignoreParentWithdrawable"]
        ]
        return {k: str(v) for k, v in result.items()}
    return result


def skill_data_fill(data):
    SP_TYPE = {
        "INCREASE_WITH_TIME": "自动回复",
        "INCREASE_WHEN_ATTACK": "攻击回复",
        "INCREASE_WHEN_TAKEN_DAMAGE": "受击回复",
        8: "被动",
    }
    SKILL_TYPE = {"PASSIVE": "被动", "MANUAL": "手动触发", "AUTO": "自动触发"}

    result = {}
    result["技能名"] = data["levels"][0]["name"]
    result["技能类型1"] = SP_TYPE[data["levels"][0]["spData"]["spType"]]

    if data["levels"][0]["spData"]["spType"] != 8:
        result["技能类型2"] = SKILL_TYPE[data["levels"][0]["skillType"]]

    if (
        "rangeId" in data["levels"][0].keys()
        and data["levels"][0]["rangeId"] is not None
    ):
        result["技能范围"] = data["levels"][0]["rangeId"]

    for i in range(0, len(data["levels"])):
        result[f"技能{i + 1}初始"] = data["levels"][i]["spData"]["initSp"]
        result[f"技能{i + 1}消耗"] = data["levels"][i]["spData"]["spCost"]

        if data["levels"][i]["duration"] > 0:
            result[f"技能{i + 1}持续"] = data["levels"][i]["duration"]

        if (
            "description" in data["levels"][i].keys()
            and data["levels"][i]["description"] is not None
        ):
            result[f"技能{i + 1}描述"] = rich_text.compile(
                BBKeyReplace().compile(
                    data["levels"][i]["description"],
                    data["levels"][i]["blackboard"],
                )
            )
        else:
            result[f"技能{i + 1}描述"] = "-"

    return {k: str(v) for k, v in result.items()}


async def generateTrapText(key, value, sem: asyncio.Semaphore, client):
    def strip(text: str):
        return text.strip() + "\n"

    async with sem:
        content = parse("")

        title = value["name"]
        # flag = 0
        # existed_content = ""
        # try:
        #     existed_content = await bot.get_page_text(title)
        # except Exception:
        #     existed_content = ""
        # if existed_content:
        #     flag += 1
        # if list(missing_traps.values()).count(title) > 1:
        #     flag += 1
        # if flag != 0:
        #     title += f"({key})"
        # 添加装置信息模板
        trap_info_template = Template("装置信息\n")
        content.append("==装置信息==\n")
        content.append(trap_info_template)

        for k, v in char_data_fill("", PATH, value).items():
            trap_info_template.add(k, strip(v))

        for k, v in (await asset_data_fill(asset_data, key, client)).items():
            trap_info_template.add(k, strip(v))

        # 添加装置技能部分
        content.append("\n==装置技能==\n")
        if value["skills"] and len(value["skills"]) > 0:
            if len(value["skills"]) > 1:
                content.append(
                    "'''{{color|red|该装置拥有多个技能，技能携带情况请查阅对应关卡！}}'''\n\n\n"
                )
            for i in range(0, len(value["skills"])):
                content.append(f"'''技能{i + 1}'''\n")
                skill_template = Template("装置技能\n")
                for k, v in skill_data_fill(
                    skill_data[value["skills"][i]["skillId"]]
                ).items():
                    skill_template.add(k, strip(v))
                content.append(skill_template)
        else:
            content.append("该装置无技能\n")

        # 添加出场关卡部分
        content.append("\n==出场关卡==\n")
        unveil_template = Template("装置出场关卡")
        if title != value["name"]:
            unveil_template.add(1, value["name"], showkey=False)
        content.append(unveil_template)

        # 添加 spine
        content.append("\n==装置模型==\n")
        spine_template = Template("spineId")
        spine_template.add("id", value["customed_trapid"])
        content.append(spine_template)

        def zipcontent(text):
            return re.sub(r"\n+", "\n", str(text))

        print(title)

        async def trapside():
            assetsdata = await asset_data_fill(asset_data, key, client)
            if assetsdata.get("阵营") is not None:
                return assetsdata.get("阵营") + "装置"
            else:
                return "我方装置"

        await asyncio.sleep(1)
        print(zipcontent(content))
        return {
            "装置名": value["name"].strip(),
            "pagetitle": title.strip(),
            "content": zipcontent(content).strip(),
            "trapid": key.strip(),
            "阵营": (await trapside()),
            "装置页面": "是" if value["name"] != title else None,
        }


async def asyncFetchJson(url):
    async with AsyncClient() as lclient:
        res = await lclient.get(url)
        return res.json()


async def asyncFetchData(url):
    async with AsyncClient() as lclient:
        res = await lclient.get(url)
        return res.read()


async def fetchWikiPages(bot):
    pagel: dict = await bot.ask(query="[[分类:装置]]|?装置id|?装置名称|limit=1000")
    pagel: dict = pagel["results"]
    cleaned_pagel = {}
    for key, value in pagel.items():
        printouts = value["printouts"]
        if not printouts["装置id"]:
            continue
        for i in printouts["装置id"]:
            cleaned_pagel[i] = {
                "id": i,
                "trapname": printouts["装置名称"][0],
                "wikipage": value["fulltext"],
            }
    existed_pages = [value["wikipage"] for key, value in cleaned_pagel.items()]
    return cleaned_pagel, existed_pages


def has_template_in_text(name: str, code: mwparserfromhell.wikicode.Wikicode) -> bool:
    for template in code.filter_templates(recursive=False):
        template = cast(mwparserfromhell.wikicode.Template, template)
        if template.name.strip() == name:
            return True
    return False


def update_trap_template_ids(
    code, trapid
) -> tuple[mwparserfromhell.wikicode.Wikicode, bool]:
    changed = False
    for template in code.filter_templates(recursive=False):
        template = cast(mwparserfromhell.wikicode.Template, template)
        if template.name.strip() == "装置信息":
            existed_ids = template.get("装置id").value.strip()
            if existed_ids:
                ids = existed_ids.split(",")
            else:
                ids = []
            if trapid not in ids:
                ids.append(trapid)
                template.add("装置id", (",".join(ids)) + "\n")
                changed = True
            break
    return code, changed


async def editTrapPage(value, sem: asyncio.Semaphore):
    # async with sem:
    await asyncio.sleep(1)
    existed_content = ""
    try:
        existed_content = await bot.get_page_text(value["pagetitle"])
    except Exception:
        existed_content = ""
    if not existed_content:
        await bot.edit_page(
            title=value["pagetitle"],
            text=value["content"],
            summary="//Edit by bot.",
            minor=True,
        )
    else:
        code = parse(existed_content)
        if has_template_in_text("装置信息", code):
            code, changed = update_trap_template_ids(code, value["trapid"])
            if changed:
                await bot.edit_page(
                    title=value["pagetitle"],
                    text=str(code),
                    summary="//Update ids by bot.",
                    minor=True,
                )
            else:
                logger.info(f"skip {value['pagetitle']}")
        else:
            alt_title = value["pagetitle"] + "(装置)"
            alt_content = ""
            try:
                alt_content = await bot.get_page_text(alt_title)
            except Exception:
                alt_content = ""
            alt_code = parse(alt_content)
            if alt_content and has_template_in_text("装置信息", alt_code):
                alt_code, changed = update_trap_template_ids(alt_code, value["trapid"])
                if changed:
                    await bot.edit_page(
                        title=alt_title,
                        text=str(alt_code),
                        summary="//Update ids by bot.",
                        minor=True,
                    )
            else:
                await bot.edit_page(
                    title=value["pagetitle"] + "(装置)",
                    text=value["content"],
                    summary="//Edit by bot.",
                    minor=True,
                )


async def load_anon(client: Client, env: Environment):
    paths = [
        *await client.resolve_by_prefix("anon/"),
        *await client.resolve_by_prefix("refs/"),
    ]
    for path in paths:
        env.load_file(path, is_dependency=True)


async def get_tokens_prefab(version: str) -> list[str]:
    resp = await asyncFetchJson(HOTUPDATE_LIST(version))
    return [
        i["name"]
        for i in resp["abInfos"]
        if i["name"].startswith("pkgrps/btl_pfb_tokens")
    ]


async def main(username: str, password: str) -> None:
    os.environ["UNITYPY_AK"] = "1"
    sem = asyncio.Semaphore(1)
    global char_data, skill_data, asset_data, rich_text, wikidata, existed_pages, all_contents, missing_traps, bot
    bot = Bot(
        sitename="PRTS",
        api="https://prts.wiki/api.php",
        index="https://prts.wiki/index.php",
        username=username,
        password=password,
    )
    await bot.login()
    # client

    char_data = arktool.read_ark_file("excel/character_table.json")
    for k, v in char_data.items():
        v["customed_trapid"] = k

    skill_data = arktool.read_ark_file("excel/skill_table.json")
    fetched_version_source = await asyncFetchJson(VERSION_SOURCE)
    resVersion = fetched_version_source["resVersion"]
    clientVersion = fetched_version_source["clientVersion"]
    client = await exporter(
        Version(res_version=resVersion, client_version=clientVersion),
        None,
        [],
        ["GameData"],
    )

    asset_data = await get_unity_env(resVersion, (await get_tokens_prefab(resVersion)))
    rich_text = RichTextStyles(arktool.read_ark_file("excel/gamedata_const.json"))
    logger.success("获取基础信息成功！")
    wikidata, existed_pages = await fetchWikiPages(bot)
    missing_traps = {
        key: value["name"].strip()
        for key, value in char_data.items()
        if key.startswith("trap_") and key not in wikidata
    }
    logger.success(f"已获取所有需要编辑的装置：{str(missing_traps)}")

    # localfix: dict = json.loads(
    #     (Path(__file__).parent / "all_contents.json").read_text(encoding="utf-8"))
    # missing_traps = {i["trapid"]: i["装置名"] for i in localfix}
    # print(missing_traps)

    # all_contents = []
    # all_contents = json.loads((Path(__file__).parent / "all_contents.json").read_text(encoding="utf-8") )

    all_contents = []
    for trapid, trapname in missing_traps.items():
        all_contents.append(
            (await generateTrapText(trapid, char_data[trapid], sem, client))
        )

    with open(Path(__file__).parent / "all_contents.json", "w", encoding="utf-8") as f:
        json.dump(all_contents, f, ensure_ascii=False, indent=2)
        logger.success("已保存all_contents到本地文件")

    for value in all_contents:
        await editTrapPage(value, sem)

    # 处理trapper部分
    await bot.edit_page(
        title="User:GuBot/temp/unwritetraps.json",
        text=json.dumps(
            list(dict.fromkeys([i["装置名"].strip() for i in all_contents])),
            ensure_ascii=False,
            indent=2,
        ),
        summary="//Edit by bot.",
    )
    await asyncio.sleep(2)
    trapsformat = {}
    for i in all_contents:
        temp = {"type": i["阵营"], "params": {}}
        if i["装置页面"]:
            temp["params"]["装置页面"] = "yes"
        trapsformat[i["装置名"]] = temp
    await bot.edit_page(
        title="User:GuBot/temp/trapsformat.json",
        text=json.dumps(trapsformat, ensure_ascii=False, indent=2),
        summary="//Edit by bot.",
    )
    print(trapsformat)
