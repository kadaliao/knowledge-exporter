import logging
from typing import Tuple


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logging.basicConfig(level=logging.WARNING)
    logger.setLevel(logging.INFO)
    return logger


def get_screen_size() -> Tuple[int, int]:
    from tkinter import Tk

    root = Tk()
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    return width, height
