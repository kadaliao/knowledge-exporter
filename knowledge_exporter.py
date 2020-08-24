import asyncio
from argparse import ArgumentParser

from tqdm import tqdm

from utils import get_logger

logger = get_logger(__name__)


def get_args():
    parser = ArgumentParser(description="下载知识付费专栏💸")
    parser.add_argument("column_id", type=int, help="专栏ID", action="store", default=280)
    parser.add_argument(
        "--username", type=str, required=True, help="用户名/手机号"
    )
    parser.add_argument(
        "--password", type=str, required=True, help="密码"
    )
    parser.add_argument(
        "--headless", type=bool, default=True, help="启用无头模式[True/False]", action="store"
    )

    args = parser.parse_args()

    return args


class KnowledgeExporter:
    def __init__(self, exporter_class):
        self.Exporter = exporter_class

    async def coro(self, column_id):
        await self.Exporter(self.headless).ensure_login(self.username, self.password)
        column, chapters, articles = await self.Exporter(
            self.headless
        ).fetch_column_info(column_id)

        logger.info(f"📖 《{column.title}》，总共 {len(articles)} 文章需要下载！")

        tasks = [
            self.Exporter(self.headless).download_article(
                article, semaphore=self.semaphore
            )
            for article in articles
        ]
        tasks = asyncio.as_completed(tasks)

        for task in tqdm(tasks, total=len(articles), ncols=80):
            # TODO 异常处理，任务取消
            title = await task
            tqdm.write(f"📄 已下载：{title}")

    def run(self):
        args = get_args()

        self.headless = args.headless
        self.username = args.username
        self.password = args.password

        concur = 5 if self.headless else 1
        self.semaphore = asyncio.Semaphore(concur)

        asyncio.get_event_loop().run_until_complete(self.coro(args.column_id))
