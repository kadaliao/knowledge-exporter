import asyncio
from argparse import ArgumentParser

from tqdm import tqdm

from utils import get_logger

logger = get_logger(__name__)


def get_args():
    parser = ArgumentParser(description="下载知识付费专栏💸")
    parser.add_argument("column_id", type=int, help="专栏ID", action="store", default=280)
    parser.add_argument("--username", type=str, required=True, help="用户名/手机号")
    parser.add_argument("--password", type=str, required=True, help="密码")
    parser.add_argument(
        "--no-headless", default=False, help="禁用无头模式", action="store_true"
    )

    args = parser.parse_args()

    return args


class KnowledgeExporter:
    def __init__(self, exporter_class):
        self._exporter_class = exporter_class

    @property
    def Exporter(self):
        return self._exporter_class(self.headless)

    async def coro(self, column_id):
        await self.Exporter.ensure_login(self.username, self.password)

        # 多等一会儿，免得后面打开的浏览器实例还未登录
        await asyncio.sleep(3)

        column, chapters, articles = await self.Exporter.fetch_column_info(column_id)

        logger.info(f"📖 《{column.title}》，总共 {len(articles)} 文章需要下载！")

        tasks = [
            self.Exporter.download_article(article, semaphore=self.semaphore)
            for article in articles
        ]
        tasks = asyncio.as_completed(tasks)

        for task in tqdm(tasks, total=len(articles), ncols=80):
            # TODO 异常处理，任务取消
            title = await task
            tqdm.write(f"📄 已下载：{title}")

    def run(self):
        args = get_args()

        self.headless = not args.no_headless
        self.username = args.username
        self.password = args.password

        concur = 5 if self.headless else 1
        self.semaphore = asyncio.Semaphore(concur)

        asyncio.get_event_loop().run_until_complete(self.coro(args.column_id))
