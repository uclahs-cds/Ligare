if __name__ != "__main__":
    raise Exception("Cannot be imported.")

import sys
from os import path
from pathlib import Path

from Ligare.programming.R.process import RProcessStepBuilder

exec_dir = path.abspath(".")

script_path = Path(exec_dir, "draw_plot.R")


with open(Path(exec_dir, "letter_segments.csv"), "rb") as f:
    data = f.read()

    executor = (
        RProcessStepBuilder()
        .with_Rscript_binary_path("/usr/bin/Rscript")
        .with_args([f"--output-type=png"])
        .with_R_script_path(script_path)
        .with_method_parameters({
            "spacing": 1.2,
            "line_width": 6,
            "color": "green",
            "background_color": "black",
        })
        .with_data(data)
    )

    (proc, img_data) = executor.execute()

    _ = sys.stdout.buffer.write(img_data)
    _ = sys.stdout.buffer.flush()
