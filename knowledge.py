#!/usr/bin/env python3

# from collections import namedtuple
from dataclasses import dataclass

# Column = namedtuple("Column", "id title")
# Chapter = namedtuple("Chapter", "id title column")
# Article = namedtuple("Article", "id title content chapter column")


@dataclass
class Column:
    id: str
    title: str


@dataclass
class Chapter:
    id: str
    title: str
    column: Column


@dataclass
class Article:
    id: str
    title: str
    chapter: Chapter = None
    column: Column = None
