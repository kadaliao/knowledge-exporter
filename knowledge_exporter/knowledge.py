#!/usr/bin/env python3

from dataclasses import dataclass


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
