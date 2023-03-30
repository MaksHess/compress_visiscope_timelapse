
import sys
import os
from pathlib import Path
import argparse

SLURM_COMMAND = """#!/usr/bin/env bash
#SBATCH --array=0-{0}%50
#SBATCH --mem=125000
#SBATCH --cpus-per-task=32
#SBATCH -e errors.txt
#SBATCH -o out.txt
#SBATCH --time=0-10:00:00

source ~/.bashrc
conda activate venv_timelapse

exec python compress_visiscope_timelapse.py $SLURM_ARRAY_TASK_ID {1} -o {2} 
"""


def main():
    CLI = argparse.ArgumentParser()
    CLI.add_argument("flds", nargs="*")
    CLI.add_argument("-o", "--out_fld", type=str)
    args = CLI.parse_args()

    command = SLURM_COMMAND.format(0, ' '.join(args.flds), args.out_fld)
    print(command)
    with open("temp.sh", "w") as f:
        f.write(command)
    os.system("sbatch temp.sh")
    os.unlink("temp.sh")


if __name__ == "__main__":
    main()