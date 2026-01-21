from httpx import AsyncClient
from jinja2 import Environment
from mwbot import utils
from pathlib import Path


async def read_prts_static_json(name: str):
    async with AsyncClient() as client:
        res = await client.get(f"https://prts.wiki/index.php?title={name}&action=raw&ctype=application/json")
        return res.json()


def clean_list_and_return_str(li: list) -> str:
    return "\n".join(map(str, list(set(li))))


def clean_text(text: str):
    lines = text.strip().split("\n")
    cleaned_lines = [line.strip() for line in lines if line]
    result = "\n".join(cleaned_lines)
    return result


def return_skill_name(skill_table, skillId: str) -> str:
    return skill_table[skillId]["levels"][0]["name"]


def get_char_name(character_table, id: str) -> str:
    return character_table[id]["name"].strip()


def deal_key(key: str) -> str:
    return key.replace("[", "__").replace("]", "__").replace(".", "__")


def get_enemy_name(enemy_handbook_table, id: str) -> str:
    return enemy_handbook_table["enemyData"][id]["name"].strip()


utilsFunctions = {
    "clean_text": clean_text,
    "clean_list_and_return_str": clean_list_and_return_str,
    "get_char_name": get_char_name,
    "deal_key": deal_key,
    "return_skill_name": return_skill_name,
    "get_enemy_name": get_enemy_name,
}

env = Environment(variable_start_string="{$", variable_end_string="$}")
env.globals.update(utilsFunctions)
TEMPLATES = utils.templates_env(
    DIR_PATH=str(Path(__file__).parent / "templates"),
    variable_start_string="{$",
    variable_end_string="$}",
)

def rend_text_from_text(ORIGINALTPLT: str, **kwargs):
    template = env.from_string(ORIGINALTPLT)
    return template.render(**kwargs)
