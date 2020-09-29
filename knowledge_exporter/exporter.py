import asyncio
import subprocess
from argparse import ArgumentParser
from shutil import rmtree

from pathvalidate import sanitize_filename
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

        print(f"📖 《{column.title}》，总共 {len(articles)} 文章需要下载！")

        tasks = [
            self.Exporter.download_article(article, semaphore=self.semaphore)
            for article in articles
        ]
        tasks = asyncio.as_completed(tasks)

        for task in tqdm(tasks, total=len(articles), ncols=80):
            # TODO 异常处理，任务取消
            title = await task
            tqdm.write(f"📄 已下载：{title}")

        if self.merge:
            cpdf_cmd = "cpdf-wrapper"
            column_folder = sanitize_filename(column.title)
            column_pdf = sanitize_filename(column.title + ".pdf")

            print('📦 开始合并专栏文章')

            subprocess.call(
                [cpdf_cmd, "-idir", column_folder, "-o", column_pdf],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            rmtree(column_folder)

        print('💐 搞定，撒花。')

    def run(self):
        asyncio.get_event_loop().run_until_complete(self.coro())
