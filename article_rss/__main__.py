import dataclasses as _dc
import logging
import typing as _ty
from datetime import datetime
from logging.config import dictConfig
from zoneinfo import ZoneInfo

import yaml
from tellurium.arguments import make_from_arguments

from .arxiv_fetcher import fetch_papers_for_date
from .llm_utils import recommend_papers
from .rss_generator import generate_rss_file


@_dc.dataclass
class Main:
    deploy_url: str
    categories: list[str]
    recommend_prompt: str
    xml_path: str
    yymmdd: _ty.Optional[str] = None
    batch_size: int = 25
    max_njobs: int = 8
    logging_config: _ty.Union[str, None] = None

    def run(self) -> None:
        if self.logging_config is not None:
            with open(self.logging_config) as f:
                config = yaml.safe_load(f)
            dictConfig(config)

        if self.yymmdd is not None:
            yymmdd = self.yymmdd
        else:
            today_jst = datetime.now(ZoneInfo("Asia/Tokyo"))
            yymmdd = today_jst.strftime("%y%m%d")
            logging.info(f"yymmdd is not specified. Using today: {yymmdd}")

        fetched_papers = fetch_papers_for_date(
            self.categories,
            datetime.strptime(yymmdd, "%y%m%d").replace(tzinfo=ZoneInfo("Asia/Tokyo")),
        )
        logging.info(f"Fetched {len(fetched_papers)} papers.")

        are_recommended = recommend_papers(
            self.recommend_prompt, fetched_papers, self.batch_size, self.max_njobs
        )
        recommended_papers = []
        for is_recommended, paper in zip(are_recommended, fetched_papers, strict=False):
            if is_recommended:
                recommended_papers.append(paper)
        logging.info(f"Recommend {len(recommended_papers)} papers.")

        generate_rss_file(
            recommended_papers,
            self.deploy_url,
            self.xml_path,
        )


if __name__ == "__main__":
    make_from_arguments(Main).run()
