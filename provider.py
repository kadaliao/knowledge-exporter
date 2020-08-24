import abc
import asyncio
from typing import List, Tuple

import pyppeteer

from knowledge import Article, Chapter, Column


class Provider(abc.ABC):
    async def _inject_js(self):
        # 无头模式下navigator.webdriver为true，将webdriver的状态值改为false
        await self.page.evaluateOnNewDocument(
            "() =>{ Object.defineProperties(navigator,{ webdriver:{ get: () => false } }) }"
        )

        # chrome属性检测，在无头模式下window.chrome属性是undefined
        await self.page.evaluateOnNewDocument(
            """() =>{ window.navigator.chrome = { runtime: {},  }; }"""
        )

        # 无头模式下Notification.permission与navigator.permissions.query会返回相反的值
        await self.page.evaluateOnNewDocument(
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
        await self.page.evaluateOnNewDocument(
            """() =>{ Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] }); }"""
        )

        # navigator.plugins会返回一个数组，里面的元素代表浏览器已安装的插件，无头浏览器通常是没有插件的
        await self.page.evaluateOnNewDocument(
            """() =>{ Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5,6], }); }"""
        )

    async def _init(self):
        """初始化浏览器"""
        # width, height = _get_screen_size()  # 获得屏幕分辨率
        width, height = 1920, 1080
        browser = await pyppeteer.launch(
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
        self.page = await browser.newPage()
        self.page.setDefaultNavigationTimeout(0)
        # 设置浏览器头部
        await self.page.setUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299"
        )
        # 浏览器窗口很大，内容显示很小，需要设定page.setViewport
        await self.page.setViewport({"width": width, "height": height})

    def __init__(self, headless: bool = True):
        self.headless = headless

    @abc.abstractmethod
    async def fetch_column_info(
        self, column_id: str
    ) -> Tuple[Column, List[Chapter], List[Article]]:
        pass

    @abc.abstractmethod
    async def download_article(
        self, article: Article, sempahore: asyncio.Semaphore
    ) -> str:
        pass

    @abc.abstractmethod
    async def _process_and_print(
        self, filename: str, show_comments: bool = False
    ) -> None:
        pass

    @abc.abstractmethod
    async def ensure_login(self, username: str, password: str) -> None:
        pass

    @abc.abstractmethod
    async def _login(self, username: str, password: str, redir_url: str = None) -> None:
        pass
