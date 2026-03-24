import json
import logging
import time
import typing as _ty

import google.genai.errors
from google import genai
from joblib import Parallel, delayed

from .arxiv_fetcher import Paper

logger = logging.getLogger(__name__)
client = genai.Client()
Model = _ty.Literal["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"]


def ask_gemini(prompt: str, model: Model) -> str:
    """
    model:
    - gemini-2.5-pro: 5RPM 100RPD
    - gemini-2.5-flash: 10RPM 250RPD
    - gemini-2.0-flash: 15RPM 200RPD
    """
    for _ in range(10):
        try:
            res = client.models.generate_content(
                model=model, contents=prompt, config={"temperature": 0.0}
            )
            assert res.text is not None
            return res.text.strip()
        except google.genai.errors.APIError as e:
            if hasattr(e, "code") and e.code in [429, 500, 502, 503]:
                logger.warning(f"Gemini API error: {e}")
                delay = 61
                if e.code == 429:
                    try:
                        delay = (
                            int(e.details["error"]["details"][-1]["retryDelay"][:-1])
                            + 1
                        )
                    except Exception as e2:
                        logger.warning(
                            f"Failed to parse retry delay: {e2}. Using default {delay} seconds."
                        )
                logger.info(f"Retrying after {delay} seconds...")
                time.sleep(delay)
                continue
            else:
                raise
    raise RuntimeError("Max retries exceeded.")


def recommend_papers_batch(
    recommend_prompt: str, papers_batch: list[Paper], wait: bool = True
) -> list[bool]:
    prompt = recommend_prompt
    for i, paper in enumerate(papers_batch):
        prompt += f"\n----------\n[{i}] {paper.title.replace('\n', ' ')}\nAbstract: {paper.summary}"
    logger.info("prompt=%s", prompt)
    res_batch = ask_gemini(prompt, "gemini-2.5-flash")
    if wait:
        time.sleep(60)
    res_batch_dict = json.loads(res_batch.replace("```json", "").replace("```", ""))
    return [res_batch_dict.get(str(i), "no") == "yes" for i in range(len(papers_batch))]


def recommend_papers(
    recommend_prompt: str, papers: list[Paper], batch_size: int = 25, max_njobs: int = 8
) -> list[bool]:
    n_batches = (len(papers) + batch_size - 1) // batch_size
    n_jobs = max(1, min(max_njobs, n_batches))

    def _get_batch(idx: int) -> list[Paper]:
        start = batch_size * idx
        end = min(batch_size * (idx + 1), len(papers))
        return papers[start:end]

    res = Parallel(n_jobs=n_jobs, backend="threading")(
        delayed(recommend_papers_batch)(recommend_prompt, _get_batch(i))
        for i in range(n_batches)
    )
    return sum(res, [])


def translate_abstract(paper: Paper, wait: bool = True) -> str:
    prompt = (
        f"以下を日本語に翻訳してください。翻訳結果のみを答えてください。\n"
        f"---\n{paper.summary}\n---"
    )
    translated = ask_gemini(prompt, "gemini-2.0-flash")
    if wait:
        time.sleep(60)
    return translated
