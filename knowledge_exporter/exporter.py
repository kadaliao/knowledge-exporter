import asyncio
import subprocess
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
        self.username = username
        self.password = password
        self.show_comments = show_comments
        self.merge = merge
        self.column_id = column_id
        self.headless = headless
        
        self.exporter = exporter_class(self.headless)

        concur = 5 if headless else 1
        self.semaphore = asyncio.Semaphore(concur)

    async def coro(self):
        try:
            await self.exporter.ensure_login(self.username, self.password)

            column, chapters, articles = await self.exporter.fetch_column_info(
                self.column_id
            )

            print(f"📖 《{column.title}》，总共 {len(articles)} 文章需要下载！")

            tasks = [
                self.exporter.download_article(article, semaphore=self.semaphore)
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
        finally:
            await self.exporter.close_browser()

    def run(self):
        asyncio.get_event_loop().run_until_complete(self.coro())