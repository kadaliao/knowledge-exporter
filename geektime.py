import asyncio
import json
import os
import random
import sys
from typing import List, Tuple

from pathvalidate import sanitize_filepath
from pyppeteer.network_manager import Request, Response

from knowledge import Article, Chapter, Column
from provider import Provider
from utils import get_logger

logger = get_logger(__name__)


class GeekTime(Provider):
    async def download_article(
        self, article: Article, semaphore: asyncio.Semaphore
    ) -> str:
        async with semaphore:
            await self._init()
            await self._inject_js()
            url = f"https://time.geekbang.org/column/article/{article.id}"
            # print(f'🔗 {url}')
            await self.page.goto(url, waitUntil=["load", "networkidle0"])

            title = await self.page.title()
            title = title.strip(" - 极客时间")

            foldername = sanitize_filepath(
                # f"{article.column.title}/{article.chapter.id}_{article.chapter.title}"
                article.column.title
            )

            os.makedirs(name=foldername, exist_ok=True)

            filename = sanitize_filepath(
                f"{foldername}/{article.chapter.id}_{article.chapter.title}_{article.id}_{article.title}"
            )
            filename = filename.replace(" ", "_")

            await self._process_and_print(filename)
            await self.page.browser.close()
            await asyncio.sleep(random.randint(1, 2))

            return title

    @classmethod
    async def create(cls, *args, **kwargs):
        self = cls(*args, **kwargs)
        await self._init()
        await self._inject_js()
        return self

    async def _process_and_print(
        self, filename: str, show_comments: bool = True
    ) -> None:

        if not show_comments:
            # TODO 支持删除评论
            pass

        script = (
            "var content = document.getElementsByClassName('simplebar-content-wrapper')[1];"
            "var body = document.getElementsByTagName('body')[0];"
            "body.innerHTML = content.innerHTML;"
        )

        await self.page.evaluate(script, force_expr=True)

        if not self.headless:
            await self.page.screenshot({"path": f"./{filename}.png"})
        else:
            await self.page.pdf(
                {"path": f"./{filename}.pdf"}, margin={"top": 32, "bottom": 32}
            )

    async def fetch_column_info(
        self, column_id: str
    ) -> Tuple[Column, List[Chapter], List[Article]]:
        await self._init()
        await self._inject_js()

        articles_data = []
        column_data = {}
        chapters_data = []

        column, chapters, articles = None, [], []

        async def intercept_request(req: Request):
            await req.continue_()

        async def intercept_response(res: Response):
            nonlocal articles_data, column_data, chapters_data
            if not (
                "v1/column/intro" in res.url
                or "v1/chapters" in res.url
                or "v1/column/articles" in res.url
            ):
                return

            json_text = await res.text()
            data = json.loads(json_text)["data"]

            if "articles" in res.url:
                articles_data = data["list"]
                logger.debug("👮 捕获到文章列表请求")
            elif "chapters" in res.url:
                chapters_data = data
                logger.debug("👮 捕获到专栏章节请求")
            elif "intro" in res.url:
                column_data = data
                logger.debug("👮 捕获到专栏介绍请求")

        # 启用拦截器
        await self.page.setRequestInterception(True)
        self.page.on("response", intercept_response)
        self.page.on("request", intercept_request)

        url = f"https://time.geekbang.org/column/intro/{column_id}"

        try:
            response = await self.page.goto(url, waitUntil=["load", "networkidle0"])

            if response.status == 404:
                logger.error("🙉 错误的专栏ID")
                sys.exit(1)

            # 点击课程目录栏
            # tab = await self.page.waitForXPath('//*[@id="app"]/div[1]/div[3]/div[1]/div[1]/a[2]')
            tab = await self.page.waitForXPath("//a[text()[contains(.,'课程目录')]]")
            await tab.click()
            await asyncio.sleep(1)

            if column_data and chapters_data and articles_data:
                column = Column(column_data["id"], column_data["column_title"])
                chapters = [Chapter(d["id"], d["title"], column) for d in chapters_data]
                chapter_id_map = {chapter.id: chapter for chapter in chapters}
                articles = [
                    Article(
                        d["id"],
                        d["article_title"],
                        chapter=chapter_id_map.get(d["chapter_id"]),
                        column=column,
                    )
                    for d in articles_data
                ]

            return column, chapters, articles

        except Exception as e:
            logger.error("⁉ 获取专栏文章列表失败：%s" % e)
            sys.exit(1)
        finally:
            # 关闭浏览器
            await self.page.browser.close()
            await asyncio.sleep(random.randint(1, 3))

    async def ensure_login(self, username: str, password: str) -> None:
        await self._init()
        await self._inject_js()

        url = "https://time.geekbang.org/column/intro/280"
        await self.page.goto(url, waitUntil=["load", "networkidle2"])

        # 点掉下线提醒的框
        confirm_box = await self.page.Jx(
            '//div[@class="confirm-box"]//a[@class="button button-primary"]'
        )

        if confirm_box:
            logger.debug("🔔 提示下线了")
            await confirm_box[0].click()
            await self.page.waitForNavigation()
            await self._login(username, password)
        else:
            logger.debug("🔕 没有提示已经下线了哎")

            # 判断是否登录
            userinfo_element = await self.page.waitForXPath('//div[@class="userinfo"]')
            userinfo_text = await self.page.evaluate(
                "(element) => element.textContent", userinfo_element
            )

            if "注册" in userinfo_text:
                logger.info("👤 账户未登录！")
                await self._login(username, password, redir_url=self.page.url)

        await self.page.browser.close()
        await asyncio.sleep(2)

    async def _login(self, username: str, password: str, redir_url: str = None) -> None:
        # 区别在于是否已经在当前页面
        if redir_url:
            url = f"https://account.geekbang.org/signin?redirect={redir_url}"
            await self.page.goto(url, waitUntil=["load", "networkidle2"])

        # 密码登录
        pwd_login_link = await self.page.waitForXPath('//a[text()="密码登录"]')
        await pwd_login_link.click()
        await asyncio.sleep(1)

        username_input = await self.page.waitForXPath(
            "//input[@type='text'][@class='nw-input']"
        )
        password_input = await self.page.waitForXPath(
            "//input[@type='password'][@class='input']"
        )
        login_link = await self.page.waitForXPath("//button[text()='登录']")

        await username_input.type(username)
        await password_input.type(password)
        await login_link.click()
        await self.page.waitForNavigation()
        logger.info("🉑 登录好了")
