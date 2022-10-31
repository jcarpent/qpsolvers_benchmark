#!/usr/bin/env python3
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

"""
Test case results.
"""

import os.path
from typing import Dict, Optional

import numpy as np
import pandas

from .problem import Problem
from .spdlog import logging
from .utils import shgeom


class Results:

    """
    Test case results.
    """

    def __init__(self, csv_path: str):
        """
        Initialize results.

        Args:
            csv_path: Persistent CSV file to load previous results from.
        """
        df = pandas.DataFrame(
            [],
            columns=[
                "problem",
                "solver",
                "settings",
                "runtime",
                "found",
                "cost_error",
                "primal_error",
            ],
        )
        if os.path.exists(csv_path):
            df = pandas.concat([df, pandas.read_csv(csv_path)])
        self.df = df
        self.csv_path = csv_path

    def write(self) -> None:
        """
        Write results to their CSV file for persistence.
        """
        logging.info(f"Test set results written to {self.csv_path}")
        self.df.to_csv(self.csv_path, index=False)

    def has(self, problem: Problem, solver: str, settings: str) -> bool:
        return (
            (self.df["problem"] == problem.name)
            & (self.df["solver"] == solver)
            & (self.df["settings"] == settings)
        ).any()

    def update(
        self,
        problem: Problem,
        solver: str,
        settings: str,
        solution: Optional[np.ndarray],
        runtime: float,
    ) -> None:
        """
        Update entry for a given (problem, solver) pair.

        Args:
            problem: Problem solved.
            solver: Solver name.
            settings: Solver settings.
            solution: Solution found by the solver.
            runtime: Duration the solver took, in seconds.
        """
        self.df = self.df.drop(
            self.df.index[
                (self.df["problem"] == problem.name)
                & (self.df["solver"] == solver)
                & (self.df["settings"] == settings)
            ]
        )
        self.df = pandas.concat(
            [
                self.df,
                pandas.DataFrame(
                    {
                        "problem": [problem.name],
                        "solver": [solver],
                        "settings": [settings],
                        "runtime": [runtime],
                        "found": [solution is not None],
                        "cost_error": [problem.cost_error(solution)],
                        "primal_error": [problem.primal_error(solution)],
                    }
                ),
            ],
            ignore_index=True,
        )

    def build_success_rate_df(self) -> pandas.DataFrame:
        """
        Build the success rate data frame.

        Returns:
            Success rate data frame.
        """
        solvers = set(self.df["solver"].to_list())
        all_settings = set(self.df["settings"].to_list())
        success_rate_df = pandas.DataFrame(
            {
                settings: {
                    solver: 100.0
                    * self.df[
                        (self.df["settings"] == settings)
                        & (self.df["solver"] == solver)
                    ]["found"]
                    .astype(float)
                    .mean()
                    for solver in solvers
                }
                for settings in all_settings
            }
        )
        success_rate_df.reindex(columns=sorted(all_settings))
        return success_rate_df.sort_index()

    def build_geometric_mean_df(
        self, time_limits: Dict[str, float]
    ) -> pandas.DataFrame:
        """
        Compute the shifted geometric mean data frame.

        Args:
            time_limits: Time limits for each solver setting.

        Note:
            Similarly to the OSQP and ProxQP benchmarks, a solver that fails to
            solve a given problem is reported as having spent maximum
            computation time on it.

        Returns:
            Shifted geometric mean data frame.
        """
        solvers = set(self.df["solver"].to_list())
        all_settings = set(self.df["settings"].to_list())

        def mean_for_settings(settings):
            means = {solver: 1e20 for solver in solvers}
            for solver in solvers:
                solver_df = self.df[
                    (self.df["solver"] == solver)
                    & (self.df["settings"] == settings)
                ]
                runtimes = np.array(
                    [
                        solver_df.at[i, "runtime"]
                        if solver_df.at[i, "found"]
                        else time_limits[settings]
                        for i in solver_df.index
                    ]
                )
                means[solver] = shgeom(runtimes)
            best_mean = np.min(list(means.values()))
            return {solver: means[solver] / best_mean for solver in solvers}

        geometric_mean_df = pandas.DataFrame(
            {
                settings: mean_for_settings(settings)
                for settings in all_settings
                if settings in time_limits
            }
        )
        geometric_mean_df.reindex(columns=sorted(all_settings))
        return geometric_mean_df.sort_index()
