#!/usr/bin/env python3
# Copyright 2023 David Kalliecharan <dave@dal.ca>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS”
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE

from argparse import ArgumentParser
from numpy import round
from pathlib import Path
import re
from rich import print
from typing import Union


def extract_cycle_num(s: str) -> int:
    cycle = re.findall(r'Cycle([\d]+)', s)
    num: Union[int, str] = cycle[0] if len(cycle) > 0 else None

    return int(num)



if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("pvdfile", type=str, help="Paraview Data Collection File")
    parser.add_argument("-v", "--vtr", type=float, default=21.167, 
                        help="VTR [mm/s]")
    parser.add_argument("-s", "--step_size", type=float, default=1, 
                        help="Step size [mm]")

    args = parser.parse_args()

    pvdfile = Path(args.pvdfile)
    vtr = args.vtr
    step_size = args.step_size

    regex_dataset = re.compile("^<DataSet.*")

    print(f"Reading {pvdfile}")
    with open(pvdfile, "r") as f:
        pvdlines = f.readlines()
        for l in pvdlines:
            m = regex_dataset.match(l)
            if m is None:
                continue

            ds = m.group()
            ts = re.findall('timestep="([\d.]+)"', ds)
            ts_dflt = ts[0] if len(ts) > 0 else None

            cyc = re.findall('file="(Cycle[\d]+)/', ds)
            cyc_dflt = cyc[0] if len(cyc) > 0 else None

    pvd_path = pvdfile.parent
    cycles = [str(p.stem) for p in sorted(list(pvd_path.glob("Cycle*")))]
    cycles.reverse()

    idx = pvdlines.index(ds + '\n')
    pvdlines.remove(ds + '\n')

    print("Inserted missing DataSets")
    for cyc in cycles:
        cycle_num = extract_cycle_num(cyc)
        elapsed_time = cycle_num * step_size / vtr
        elapsed_time = round(elapsed_time, 4)
        elapsed_time = f"{elapsed_time:0.4f}"

        ds_updated = ds.replace(ts_dflt, elapsed_time).replace(cyc_dflt, cyc)
        pvdlines.insert(3, ds_updated + '\n') 

    new_pvdfile = pvd_path / (pvdfile.stem + "_updated" + pvdfile.suffix)
    with open(new_pvdfile, "w") as f:
        text = "".join(pvdlines)
        f.write(text)
    print("Finished")
