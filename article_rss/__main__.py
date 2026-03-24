import dataclasses as _dc
import typing as _ty
from logging.config import dictConfig

import yaml
from tellurium.arguments import make_from_arguments

from . import square


@_dc.dataclass
class Main:
    n: int
    logging_config: _ty.Union[str, None]

    def run(self) -> None:
        if self.logging_config is not None:
            with open(self.logging_config) as f:
                config = yaml.safe_load(f)
            dictConfig(config)
        print(square(self.n))


if __name__ == "__main__":
    make_from_arguments(Main).run()
