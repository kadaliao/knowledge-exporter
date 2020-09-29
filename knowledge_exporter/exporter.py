import asyncio
from argparse import ArgumentParser

from tqdm import tqdm

from .utils import get_logger

logger = get_logger(__name__)


class KnowledgeExporter:
    def __init__(
        self,
        exporter_class,
        username,
        password,
        column_id,
        show_comments=True,
        merge=True,
        headless=True,
    ):
        self.exporter_class = exporter_class
        self.username = username
        self.password = password
        self.show_comments = show_comments
        self.merge = merge
        self.column_id = column_id
        self.headless = headless

        concur = 5 if headless else 1
        self.semaphore = asyncio.Semaphore(concur)

    @property
    def Exporter(self):
        return self.exporter_class(self.headless)

    async def coro(self):
        await self.Exporter.ensure_login(self.username, self.password)

        # 多等一会儿，免得后面打开的浏览器实例还未登录
        await asyncio.sleep(3)

        column, chapters, articles = await self.Exporter.fetch_column_info(
            self.column_id
        )

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
        asyncio.get_event_loop().run_until_complete(self.coro())
