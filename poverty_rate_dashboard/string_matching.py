from itertools import product
from typing import Callable, Iterable, List, Union

import numpy as np
import pandas as pd
import textdistance
from glom import Merge, T, glom
from scipy.optimize import linear_sum_assignment


def fuzzy_matching_best(
    source: Iterable,
    target: List[str],
    key: Callable = lambda x: x,
    scorer: Callable = textdistance.jaro_winkler.distance,
    maximize: bool = False,
):
    # The key functionality is added thanks to https://stackoverflow.com/a/18296812

    diff_source = source
    diff_target = target

    pairs = product(diff_source, diff_target)

    scores = np.array([scorer(key(q), c) for q, c in pairs]).reshape(
        (len(diff_source), len(diff_target))
    )

    row_ind, col_ind = linear_sum_assignment(scores, maximize)

    return [
        {"source": diff_source[i], "target": diff_target[j], "distance": scores[i, j]}
        for i, j in zip(row_ind, col_ind)
    ]


def fuzzy_match(
    df: pd.DataFrame,
    source_column: Union[str, int],
    target: Iterable[str],
    scorer: Callable = textdistance.jaro_winkler.distance,
    key: Callable = lambda x: x,
    maximize: bool = False,
    debug=False,
):
    source = df[source_column].astype("str").unique()

    source_diff = list(set(source) - set(target))
    target_diff = list(set(target) - set(source))

    matches = fuzzy_matching_best(
        source=source_diff,
        target=target_diff,
        key=key,
        scorer=scorer,
        maximize=maximize,
    )

    replacements_spec = Merge([{T["source"]: "target"}])
    replacements_dict = glom(matches, replacements_spec)

    distances_spec = ([{T["source"]: "distance"}], Merge())
    distances_dict = glom(matches, distances_spec)

    if debug:
        debug_col_name = f"{source_column}_match_from_target"
        return df.pipe(
            lambda df: df.assign(
                **{
                    debug_col_name: df[source_column].replace(replacements_dict),
                    "distance": df[source_column]
                    .replace(distances_dict)
                    .replace(r"\D+", 0, regex=True),
                }
            )
        ).set_index([source_column, debug_col_name, "distance"])
    else:
        return df.pipe(
            lambda df: df.assign(
                **{source_column: df[source_column].replace(replacements_dict)}
            )
        )


def sequential_fuzzy_match(
    df: pd.DataFrame,
    source_cols: List[Union[str, int]],
    target_cols: List[Iterable],
    *args,
    **kwargs,
) -> pd.DataFrame:
    result_df = df.copy()
    for source_col, target_col in zip(source_cols, target_cols):
        result_df = fuzzy_match(result_df, source_col, target_col, *args, **kwargs)
    return result_df
