from argparse import ArgumentParser

import click

from .exporter import KnowledgeExporter
from .geektime import GeekTime

PROVIDERS = [GeekTime]

provider_map = {provider.__name__: provider for provider in PROVIDERS}


@click.command(help="📑 -> 📚 导出知识付费平台内容", no_args_is_help=True)
@click.option(
    "-t",
    "--target",
    type=click.Choice(provider_map.keys(), case_sensitive=False),
    required=True,
    help="知识付费平台",
)
@click.option("-u", "--username", required=True, help="手机号/用户名")
@click.option("-p", "--password", required=True, help="密码")
@click.option("--merge/--no-merge", default=True, help="合并专栏文章")
@click.option("--headless/--head", default=True, help="使用无头浏览器", hidden=True)
@click.option("--show-comments/--no-comments", default=True, help="显示文章评论", hidden=True)
@click.argument("column_id", type=int, required=True)
def main(**kwargs):
    target = kwargs.pop("target")
    exporter_class = provider_map[target]
    app = KnowledgeExporter(exporter_class, **kwargs)
    app.run()


__all__ = ["main"]
