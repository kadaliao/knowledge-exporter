import abc
import asyncio
from typing import List, Tuple, Optional

import pyppeteer
from pyppeteer.browser import Browser
from pyppeteer.page import Page

from .knowledge import Article, Chapter, Column


class Provider(abc.ABC):
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.cookies = {}
        self.browser: Optional[Browser] = None

    async def _inject_js(self, page: Page):
        # 无头模式下navigator.webdriver为true，将webdriver的状态值改为false
        await page.evaluateOnNewDocument(
            "() =>{ Object.defineProperties(navigator,{ webdriver:{ get: () => false } }) }"
        )

        # chrome属性检测，在无头模式下window.chrome属性是undefined
        await page.evaluateOnNewDocument(
            """() =>{ window.navigator.chrome = { runtime: {},  }; }"""
        )

        # 无头模式下Notification.permission与navigator.permissions.query会返回相反的值
        await page.evaluateOnNewDocument(
            """() => {
                  const originalQuery = window.navigator.permissions.query;
                  return window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                      Promise.resolve({ state: Notification.permission }) :
                      originalQuery(parameters)
                  );
                }
            """
        )

        # navigator.languages可以获取一个数组，里面存储的是浏览器用户所有的次选语言。而无头浏览器的navigator.languages返回的是空字符串
        await page.evaluateOnNewDocument(
            """() =>{ Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] }); }"""
        )

        # navigator.plugins会返回一个数组，里面的元��代表浏览器已安装的插件，无头浏览器通常是没有插件的
        await page.evaluateOnNewDocument(
            """() =>{ Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5,6], }); }"""
        )

    async def launch_browser(self):
        """初始化浏览器"""
        if self.browser:
            return

        width, height = 1920, 1080
        self.browser = await pyppeteer.launch(
            {
                "headless": self.headless,
                # 'userDataDir': './userdata',
                "args": [
                    # 只有headless=False时才需要设置该参数
                    "--window-size={},{}".format(width, height),
                    "--disable-extensions",
                    "--hide-scrollbars",
                    "--disable-bundled-ppapi-flash",
                    "--mute-audio",  # 页面静音
                    "--no-sandbox",  # 以最高权限运行
                    "--disable-setuid-sandbox",
                    "--disable-gpu",
                    "--disable-infobars",
                ],
                "ignoreHTTPSErrors": True,
                "dumpio": False,  # chromium浏览器多开页面卡死问题，解决这个问题的方法就是浏览器初始化的时候添加'dumpio':True。
                "userDataDir": "./userdata",  # 设置用户目录,进行cookies的保存，下次打开可以免登录。如果没有设置，每次打开就是一个全新的浏览器
            }
        )

    async def close_browser(self):
        if self.browser:
            await self.browser.close()
            self.browser = None

    async def _inject_cookies(self, page: Page):
        for cookie in self.cookies:
            await page.setCookie(cookie)

    async def create_page(self) -> Page:
        if not self.browser:
            await self.launch_browser()
        
        page = await self.browser.newPage()
        # 设置浏览器头部
        await page.setUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299"
        )
        # 浏览器窗口很大，内容显示很小，需要设定page.setViewport
        await page.setViewport({"width": 1920, "height": 1080})
        
        await self._inject_js(page)
        await self._inject_cookies(page)
        return page

    @abc.abstractmethod
    async def fetch_column_info(
        self, column_id: str
    ) -> Tuple[Column, List[Chapter], List[Article]]:
        pass

    @abc.abstractmethod
    async def download_article(
        self, article: Article, semaphore: asyncio.Semaphore
    ) -> str:
        pass

    @abc.abstractmethod
    async def ensure_login(self, username: str, password: str) -> None:
        pass