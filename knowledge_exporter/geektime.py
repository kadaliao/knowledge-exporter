import asyncio
import json
import os
import random
import sys
from typing import List, Tuple

from pathvalidate import sanitize_filename, sanitize_filepath
from pyppeteer.errors import TimeoutError
from pyppeteer.network_manager import Request, Response
from pyppeteer.page import Page

from .knowledge import Article, Chapter, Column
from .provider import Provider
from .utils import get_logger

logger = get_logger(__name__)


class GeekTime(Provider):
    async def download_article(
        self, article: Article, semaphore: asyncio.Semaphore
    ) -> str:
        async with semaphore:
            page = await self.create_page()
            try:
                url = f"https://time.geekbang.org/column/article/{article.id}"
                # print(f'🔗 {url}')
                await page.goto(url, waitUntil=["load", "networkidle0"])

                title = await page.title()
                title = title.strip(" - 极客��间")

                foldername = sanitize_filename(article.column.title)
                os.makedirs(name=foldername, exist_ok=True)

                filename = sanitize_filename(
                    f"{article.chapter.id}_{article.chapter.title}_{article.id}_{article.title}"
                )
                filename = filename.replace(" ", "_")

                filename = sanitize_filepath(f"{foldername}/{filename}")

                await self._process_and_print(page, filename)
                await asyncio.sleep(random.randint(1, 2))
                return title
            finally:
                await page.close()

    async def _process_and_print(
        self, page: Page, filename: str, show_comments: bool = True
    ) -> None:

        if not show_comments:
            # TODO 支持删除评论
            pass

        script = (
            "var content = document.getElementsByClassName('simplebar-content-wrapper')[1];"
            "var body = document.getElementsByTagName('body')[0];"
            "body.innerHTML = content.innerHTML;"
        )

        try:
            await page.evaluate(script, force_expr=True)
        except Exception as e:
            logger.warning(f"Error evaluating script on {filename}: {e}")

        if not self.headless:
            await page.screenshot({"path": f"./{filename}.png"})
        else:
            await page.pdf(
                {"path": f"./{filename}.pdf"}, margin={"top": 32, "bottom": 32}
            )

    async def fetch_column_info(
        self, column_id: str
    ) -> Tuple[Column, List[Chapter], List[Article]]:
        
        page = await self.create_page()
        try:
            articles_data = []
            column_data = {}
            chapters_data = []

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

                try:
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
                except Exception:
                    pass

            # 启用拦截器
            await page.setRequestInterception(True)
            page.on("response", intercept_response)
            page.on("request", intercept_request)

            url = f"https://time.geekbang.org/column/intro/{column_id}"

            response = await page.goto(url, waitUntil=["load", "networkidle0"])

            if not response or response.status == 404:
                print("🙉 错误的专栏ID")
                # Instead of sys.exit, we should probably raise exception, but following pattern
                raise ValueError("错误的专栏ID")

            # 点击课程目录栏
            try:
                tab = await page.waitForXPath("//a[text()[contains(.,'课程目录')]]")
                await tab.click()
                await asyncio.sleep(1)
            except TimeoutError:
                logger.warning("Could not find '课程目录' tab, maybe already there or different layout.")

            # Wait a bit for responses to be intercepted
            await asyncio.sleep(2)

            column = None
            chapters = []
            articles = []

            if column_data and chapters_data and articles_data:
                column = Column(str(column_data["id"]), column_data["column_title"])
                chapters = [Chapter(str(d["id"]), d["title"], column) for d in chapters_data]
                chapter_id_map = {chapter.id: chapter for chapter in chapters}
                articles = [
                    Article(
                        str(d["id"]),
                        d["article_title"],
                        chapter=chapter_id_map.get(str(d["chapter_id"])),
                        column=column,
                    )
                    for d in articles_data
                ]
            else:
                 raise RuntimeError("未能获取到完整的专栏信息 (column, chapters, or articles missing)")

            return column, chapters, articles

        except Exception as e:
            print("⁉ 获取专栏文章列表失败：%s" % e)
            sys.exit(1)
        finally:
            await page.close()
            await asyncio.sleep(random.randint(1, 3))

    async def ensure_login(self, username: str, password: str) -> None:
        page = await self.create_page()
        try:
            url = "https://time.geekbang.org/column/intro/280"
            await page.goto(url, waitUntil=["load", "networkidle2"])

            # 点掉下线提醒的框
            confirm_box = await page.Jx(
                '//div[@class="confirm-box"]//a[@class="button button-primary"]'
            )

            if confirm_box:
                logger.debug("🔔 提示下线了")
                await confirm_box[0].click()
                await page.waitForNavigation()
                await self._login(page, username, password)
            else:
                logger.debug("🔕 没有提示已经下线了哎")

                # 判断是否登录
                try:
                    userinfo_element = await page.waitForXPath('//div[@class="userinfo"]', timeout=5000)
                    userinfo_text = await page.evaluate(
                        "(element) => element.textContent", userinfo_element
                    )
                    
                    if "注册" in userinfo_text:
                        print("👤 账户未登录！")
                        await self._login(page, username, password, redir_url=page.url)
                except TimeoutError:
                     print("👤 无法检测登录状态 (Timeout)，尝试直接登录")
                     await self._login(page, username, password, redir_url=page.url)


            self.cookies = await page.cookies()
        finally:
            await page.close()
            await asyncio.sleep(2)

    async def _login(self, page: Page, username: str, password: str, redir_url: str = None) -> None:
        # 区别在于是否已经在当前页面
        if redir_url:
            url = f"https://account.geekbang.org/signin?redirect={redir_url}"
            await page.goto(url, waitUntil=["load", "networkidle2"])

        # 密码登录
        try:
            pwd_login_link = await page.waitForXPath('//a[text()="密码登录"]')
            await pwd_login_link.click()
            await asyncio.sleep(1)
        except TimeoutError:
            # Maybe already on password login or different layout
            pass

        username_input = await page.waitForXPath(
            "//input[@type='text'][@class='nw-input']"
        )
        password_input = await page.waitForXPath(
            "//input[@type='password'][@class='input']"
        )
        login_link = await page.waitForXPath("//button[text()='登录']")

        await username_input.type(username)
        await password_input.type(password)

        try:
            page.setDefaultNavigationTimeout(10000)
            await login_link.click()
            await page.waitForNavigation()
            print("🉑 登录好���")
        except TimeoutError:
            print("🆘 登录失败，请确保手机号、密码正确，可使用 --head 开启浏览器尝试")
            sys.exit(1)