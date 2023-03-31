import argparse
import os
import sys
from pathlib import Path

from compress_visiscope_timelapse import _parse_sites_multiple_folders

SLURM_COMMAND = """#!/usr/bin/env bash
#SBATCH --array=0-{0}%10
#SBATCH --mem=125000
#SBATCH --cpus-per-task=8
#SBATCH -e errors.txt
#SBATCH -o out.txt
#SBATCH --time=0-10:00:00

source ~/.bashrc
conda activate venv_timelapse

exec python compress_visiscope_timelapse.py $SLURM_ARRAY_TASK_ID {1} -o {2} 
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("flds", nargs="*")
    parser.add_argument("-o", "--out_fld", type=str)
    args = parser.parse_args()

    sites = _parse_sites_multiple_folders(args.flds)

    command = SLURM_COMMAND.format(len(sites) - 1, " ".join(args.flds), args.out_fld)
    print(command)
    with open("temp.sh", "w") as f:
        f.write(command)
    os.system("sbatch temp.sh")
    os.unlink("temp.sh")


if __name__ == "__main__":
    main()
