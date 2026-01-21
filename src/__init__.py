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

@cli_group.command("trapedit")
@click.option("--username", "-u", help="bot name")
@click.option("--password", "-w", help="bot password")
def _trapedit(username: str, password: str) -> None:
    from trapedit import main as perform_action

    coro = partial(perform_action, username=username, password=password)
    anyio.run(coro)


@cli_group.command("testlogin")
@click.option("--username", "-u", help="bot name")
@click.option("--password", "-w", help="bot password")
def _testlogin(username: str, password: str) -> None:
    from testlogin import main as perform_action

    coro = partial(perform_action, username=username, password=password)
    anyio.run(coro)


@cli_group.command("trapedit_test")
@click.option("--page", "-p", help="需要测试的页面")
@click.option("--username", "-u", help="bot name")
@click.option("--password", "-w", help="bot password")
def _trapedit_test(page: str, username: str, password: str) -> None:
    from trapstage import test as perform_action

    coro = partial(perform_action, page=page, username=username, password=password)
    anyio.run(coro)

def main():
	try:
		cli_group()
	except Exception as e:
		click.echo(f'Error: {e}', err=True)
		sys.exit(1)


if __name__ == '__main__':
	main()

