import logging

from feedgen.feed import FeedGenerator

from .arxiv_fetcher import Paper

logger = logging.getLogger(__name__)


def generate_rss_file(papers: list[Paper], deploy_url: str, output_path: str) -> None:
    fg = FeedGenerator()
    fg.id(deploy_url)
    fg.link(href=deploy_url, rel="alternate")
    title = "Today's arXiv"
    fg.title(title)
    fg.description(title)
    fg.language("ja")

    for paper in papers:
        fe = fg.add_entry()
        fe.id(paper.id)
        fe.title(paper.title)
        fe.link(href=paper.link)
        fe.pubDate(paper.updated)
        fe.description(paper.summary + "\n" + ", ".join(paper.authors))

    fg.rss_file(output_path)
    logger.info("RSS written to %s", output_path)
