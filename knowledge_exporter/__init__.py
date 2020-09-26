from .exporter import KnowledgeExporter
from .geektime import GeekTime


def main():
    app = KnowledgeExporter(GeekTime)
    app.run()


__all__ = ["main"]
