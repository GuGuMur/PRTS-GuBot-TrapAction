import mwparserfromhell
from mwbot import arktool
from copy import deepcopy
from trapstage.source.utils import (
    # read_prts_static_json,
    clean_list_and_return_str,
    clean_text,
    return_skill_name,
    # get_char_name,
    deal_key,
    # get_enemy_name,
    env,
    utilsFunctions,
    TEMPLATES,
    rend_text_from_text,
)  # noqa: F403
# from typing import Union
# from loguru import logger

# arktool.GameDataPosition = "E:/ArknightsGameData/zh_CN/gamedata"
# unwritetiles = ""
# tilesformat = ""
# unwritetraps = ""
# trapsformat = ""


def cell_deal_token(data: dict) -> dict:
    charinfo = character_table[data["inst"]["characterKey"]]
    result = {}
    result.update(**utilsFunctions)
    result["装置名称"] = char.get_char_name(data["inst"]["characterKey"]).strip()

    # 从global里直接获取的内容-gamedata
    result["gamedata"] = {
        "character_table": character_table,
        "skill_table": skill_table,
        "enemy_handbook_table": enemy_handbook_table,
    }
    # 能从json中直接获取的内容
    if data["inst"]["level"]:
        result["装置等级"] = data["inst"]["level"]
    if data.get("initialCnt"):
        result["装置可部署数量"] = data["initialCnt"]
    if data.get("skillIndex") is not None and data["skillIndex"] != -1:
        charskillid_local = charinfo["skills"][data["skillIndex"]]["skillId"]
        result["装置技能"] = return_skill_name(skill_table, charskillid_local)
    if data.get("mainSkillLvl"):
        result["技能等级"] = data["mainSkillLvl"]
    result.update(data)
    # 需要与static内容联动的内容
    # 处理一下装置到底用不用
    if result["装置名称"] in unwritetraps:
        result.update(data)
        return {
            "type": "不需要写入页面的装置",
            "text": clean_text(TEMPLATES.render(T_NAME="trapper.jinja2", **result)),
        }
    else:
        if result["装置名称"] in trapsformat.keys():
            copy_trapsformat = deepcopy(trapsformat)
            trap_cell_format = copy_trapsformat[str(result["装置名称"])]
            # logger.debug(trap_cell_format)
            traptype = trap_cell_format["type"]
            if trap_cell_format.get("settings", {}).get("displaySkill", True) is False:
                try:
                    result.pop("装置技能")
                    result.pop("技能等级")
                except KeyError:
                    pass
            for k, v in trap_cell_format["params"].items():
                if isinstance(v, list):
                    v_divider = "<br/>"  # value_dealt

                    if v and isinstance(v[0], dict):
                        v_divider = str(v[0].get("divider", "<br/>"))
                    v_result = v_divider.join(
                        [item for item in v if isinstance(item, str)]
                    )
                    trap_cell_format["params"][k] = rend_text_from_text(
                        ORIGINALTPLT=v_result, **result
                    )

                else:
                    trap_cell_format["params"][k] = rend_text_from_text(
                        ORIGINALTPLT=v, **result
                    )

            def clean_param(text: str) -> str:
                return clean_text(text.strip()).replace("\n", "<br/>")

            addition_text = [
                f"|{k}={clean_param(v)}" for k, v in trap_cell_format["params"].items()
            ]
            result["附加文本"] = "\n".join(addition_text)
        else:
            traptype = "未分类装置"
            hint.append(
                f"没有获取到装置 [{result['装置名称']}, {data['inst']['characterKey']}] 的应用！<br/>"
            )
            result["附加文本"] = ""
        return {
            "type": traptype,
            "name": result["装置名称"],
            "text": clean_text(TEMPLATES.render(T_NAME="trapper.jinja2", **result)),
        }


def deal_token(stageinfo: dict, unedittrap: bool = True) -> str:
    trap_collection: dict[str, list[str]] = {}
    result_text: str = ""
    mainparams = ["predefines", "hardPredefines"]
    subparams = ["tokenInsts", "tokenCards"]

    for maintitle in mainparams:
        if subdict := stageinfo.get(maintitle, False):
            for subtitle in subparams:
                if nextdict := subdict.get(subtitle, False):
                    for t in nextdict:
                        cell_trap_info = cell_deal_token(data=t)
                        if cell_trap_info.get("name", None) in had_trap:
                            continue
                        trap_collection.setdefault(cell_trap_info["type"], []).append(
                            cell_trap_info["text"]
                        )

    if trap_collection:
        if not unedittrap:
            trap_collection.pop("不需要写入页面的装置", None)
        for k, v in trap_collection.items():
            result_text += f"=={k}==\n" + "\n".join(list(set(v)))
            result_text += "\n"
        return clean_text(result_text)
    else:
        return ""


def deal_tiles(stageinfo: dict):
    text_list = []
    for i in stageinfo["mapData"]["tiles"]:
        # 处理新tiles
        if i["tileKey"] not in unwritetiles:
            # 选择tile的处理方式
            if i["tileKey"] in tilesformat:
                template = env.from_string(tilesformat[i["tileKey"]])
                if i["blackboard"]:
                    data = {
                        deal_key(cell["key"]): cell["value"] for cell in i["blackboard"]
                    }
                else:
                    data = {}
                text = template.render(**data)
                text_list.append(text)
            # else:
            #     continue
            else:
                hint.append(f"没有获取到tile [{i['tileKey']}]的应用！<br/>")
                continue
    if text_list:
        tiletext = clean_list_and_return_str(text_list)
        return tiletext
    else:
        return ""


async def return_text(
    pagetext: str,
    unwritetiles1,
    tilesformat1,
    unwritetraps1,
    trapsformat1,
    unedittrap: bool = True,
):
    global \
        unwritetiles, \
        tilesformat, \
        character_table, \
        trapsformat, \
        unwritetraps, \
        had_trap
    global \
        skill_table, \
        env, \
        TEMPLATES, \
        new_tiles_table, \
        arktool, \
        hint, \
        char, \
        enemy_handbook_table
    # 首先处理stage
    stage_id = arktool.get_stage_id(content=pagetext)
    if stage_id:
        ...  # continue
    else:
        return {"status": False, "text": pagetext, "hint": ""}
    # 然后再开始获取数据
    char = arktool.char()
    character_table = arktool.read_ark_file("excel/character_table.json")
    skill_table = arktool.read_ark_file("excel/skill_table.json")
    enemy_handbook_table = arktool.read_ark_file("excel/enemy_handbook_table.json")
    new_tiles_table = {}
    # unwritetiles = await read_prts_static_json("特殊地形/trapper/unwritetiles.json")
    # tilesformat = await read_prts_static_json("特殊地形/trapper/tilesformat.json")
    # unwritetraps = await read_prts_static_json(
    #     "模板:关卡装置/trapper/unwritetraps.json"
    # )
    # trapsformat = await read_prts_static_json("模板:关卡装置/trapper/trapsformat.json")
    # if not unwritetiles:
    #     unwritetiles = await read_prts_static_json("特殊地形/trapper/unwritetiles.json")
    # if not tilesformat:
    #     tilesformat = await read_prts_static_json("特殊地形/trapper/tilesformat.json")
    # if not unwritetraps:
    #     unwritetraps = await read_prts_static_json(
    #         "模板:关卡装置/trapper/unwritetraps.json"
    #     )
    # if not trapsformat:
    #     trapsformat = await read_prts_static_json("模板:关卡装置/trapper/trapsformat.json")
    unwritetiles = unwritetiles1
    tilesformat = tilesformat1
    trapsformat = trapsformat1
    unwritetraps = unwritetraps1
    hint = []
    wikicode = pagetext[:]
    had_trap = []
    parsedwikitext = mwparserfromhell.parse(pagetext)
    for template in parsedwikitext.filter_templates():
        if template.name.matches("关卡装置"):
            had_trap.append(template.get("装置名称").value.strip())
            continue
    try:
        stageinfo = arktool.get_stage_info(content=pagetext)
        tiletext = deal_tiles(stageinfo=stageinfo)
        tokentext = deal_token(stageinfo=stageinfo, unedittrap=unedittrap)

        if tokentext:
            if "==作战进度奖励==" in wikicode:
                wikicode = wikicode.replace(
                    "==作战进度奖励==", f"{tokentext}\n==作战进度奖励=="
                )
            elif "==材料掉落==" in wikicode:
                wikicode = wikicode.replace(
                    "==材料掉落==", f"{tokentext}\n==材料掉落=="
                )
            else:
                wikicode = wikicode.replace(
                    "==注释与链接==", f"{tokentext}\n==注释与链接=="
                )
        else:
            pass
        # --------------------------------------------------
        if tiletext:
            wikicode = mwparserfromhell.parse(wikicode)
            for template in wikicode.filter_templates():
                if template.name.matches("普通关卡信息") or template.name.matches(
                    "剿灭关卡信息"
                ):
                    template.add("特殊地形效果", f"{tiletext}")
                    continue
            wikicode = str(wikicode)
        else:
            pass
        # FINALLY!
        hint = "\n".join(list(set(hint)))
        if pagetext != wikicode:
            return {"status": True, "text": wikicode, "hint": hint}
        else:
            return {"status": False, "text": wikicode, "hint": hint}
    except Exception as e:
        import traceback

        traceback.print_exc()
        hint.append(f"关卡出现bug！<br/>{e}")
        hint = "\n".join(list(set(hint)))
        return {"status": False, "text": pagetext, "hint": hint}
