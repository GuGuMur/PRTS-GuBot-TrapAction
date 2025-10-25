# ALL DATA

URL = "https://prts.wiki/api.php"
CHAR_SOURCE = "https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/character_table.json"
SKILL_SOURCE = "https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/skill_table.json"
CONST_SOURCE = "https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/gamedata_const.json"
VERSION_SOURCE = "https://ak-conf.hypergryph.com/config/prod/official/Android/version"


def ASSET_SOURCE(version: str, path: str):
    # return "https://ak.hycdn.cn/assetbundle/official/Android/assets/%s/battle_prefabs_[uc]tokens.dat" % version
    pathx = path.replace("/", "_").replace(".ab", ".dat")
    return f"https://ak.hycdn.cn/assetbundle/official/Android/assets/{version}/{pathx}"


# ASSET_PATH = "battle/prefabs_[uc]tokens.ab"


def HOTUPDATE_LIST(version):
    return (
        "https://ak.hycdn.cn/assetbundle/official/Android/assets/%s/hot_update_list.json"
        % version
    )


PATH = {
    "customed_trapid": "装置id",  # 匠心手加
    "name": "名称",
    "description": "描述",
    "appellation": "英文名",
    "phases": {
        0: {
            "rangeId": "攻击范围",
            "attributesKeyFrames": {
                0: {
                    "level": "阶段1等级",
                    "data": {
                        "maxHp": "阶段1生命值",
                        "atk": "阶段1攻击力",
                        "def": "阶段1防御力",
                        "magicResistance": "阶段1法术抗性",
                        "cost": "部署费用",
                        "blockCnt": "阻挡数",
                        "baseAttackTime": "攻击间隔",
                        "respawnTime": "再部署时间",
                        "spRecoveryPerSec": "技力恢复速度",
                        "tauntLevel": "嘲讽等级",
                        "stunImmune": "眩晕抗性",
                        "silenceImmune": "沉默抗性",
                        "sleepImmune": "沉睡抗性",
                        "frozenImmune": "冻结抗性",
                    },
                },
                1: {
                    "level": "阶段2等级",
                    "data": {
                        "maxHp": "阶段2生命值",
                        "atk": "阶段2攻击力",
                        "def": "阶段2防御力",
                        "magicResistance": "阶段2法术抗性",
                    },
                },
            },
        }
    },
    "talents": {
        0: {
            "candidates": {
                0: {
                    "unlockCondition": {"level": "天赋解锁等级"},
                    "name": "天赋名称",
                    "description": "天赋描述",
                }
            }
        }
    },
}
