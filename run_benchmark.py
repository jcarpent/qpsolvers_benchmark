#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2022 Stéphane Caron
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os

from qpsolvers import available_solvers

from qpsolvers_benchmark.test_sets import MarosMeszaros


def parse_command_line_arguments():
    parser = argparse.ArgumentParser(
        description="Benchmark quadratic programming solvers"
    )
    parser.add_argument(
        "--problem",
        "-p",
        help="Limit tests to a specific problem",
    )
    parser.add_argument(
        "--solver",
        "-s",
        help="Limit tests to a specific solver",
    )
    parser.add_argument(
        "--time-limit",
        default=10.0,
        type=float,
        help="Maximum time a solver may take to solve one problem, in seconds",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_command_line_arguments()
    solver_settings = {solver: {} for solver in available_solvers}
    solver_settings.update({"gurobi": {}, "highs": {}, "osqp": {}, "scs": {}})

    # Time limit
    solver_settings["gurobi"]["time_limit"] = args.time_limit
    solver_settings["highs"]["time_limit"] = args.time_limit
    solver_settings["osqp"]["time_limit"] = args.time_limit
    solver_settings["scs"]["time_limit_secs"] = args.time_limit

    solver_settings["osqp"] = {"eps_abs": 1e-5, "eps_rel": 0.0}

    test_set = MarosMeszaros(
        data_dir=os.path.join(
            os.path.dirname(__file__), "data", "maros_meszaros"
        ),
        results_dir=os.path.join(os.path.dirname(__file__), "results"),
    )

    test_set.run(
        solver_settings=solver_settings,
        only_problem=args.problem,
        only_solver=args.solver,
    )
    test_set.write_results()
    test_set.write_report()
