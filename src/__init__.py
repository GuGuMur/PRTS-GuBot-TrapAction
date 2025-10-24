import sys
import click
import anyio
from functools import partial


@click.group()
def cli_group():
	pass


@cli_group.command('trapstage')
@click.option(
    "--page",
    "-p",
    default="首页/新增关卡",
    show_default=True,
    help="哪里有一堆需要处理的关卡页面",
)
@click.option('--username', '-u', help='bot name')
@click.option('--password', '-w', help='bot password')
def _trapstage(page: str, username: str, password: str) -> None:
	from trapstage import main as perform_action
	coro = partial(perform_action, page=page, username=username, password=password)
	anyio.run(coro)

@cli_group.command('trapedit')
@click.option("--username", "-u", help="bot name")
@click.option("--password", "-w", help="bot password")
def _trapedit(username: str, password: str) -> None:
    from trapedit import main as perform_action

    coro = partial(perform_action, username=username, password=password)
    anyio.run(coro)


def main():
	"""导出给外部运行的 main 入口。"""
	try:
		cli_group()
	except Exception as e:
		click.echo(f'Error: {e}', err=True)
		sys.exit(1)


if __name__ == '__main__':
	main()

