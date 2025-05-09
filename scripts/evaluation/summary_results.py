"""
This script includes various functions used to prepare some of the tables in the 
main body of the paper. 
"""

# %%
import os

os.chdir("../..")
import polars as pl

from src.utils.constants import GROUPING_KEYS, REFERENCE_CONFIG
from src.utils.logging import prepare_full_time_run


def diff_fold_vs_fold(df, key):
    all_variables = [k for k in REFERENCE_CONFIG.keys()]

    r = (
        df.join(df.filter(**REFERENCE_CONFIG), on=key)
        .with_columns(
            diff_metric=pl.col("prediction_metric") - pl.col("prediction_metric_right"),
            diff_time=pl.col("time_run") / pl.col("time_run_right"),
        )
        .group_by(all_variables)
        .agg(
            metric_median=pl.median("diff_metric") * 100,
            time_median=pl.median("diff_time"),
            metric_mean=pl.mean("diff_metric") * 100,
        )
        .sort("metric_median", descending=True)
    )
    return r


def get_total_runtime(df_master):
    time_ = (
        df_master.group_by(GROUPING_KEYS)
        .agg(pl.col("time_run").mean())
        .group_by("chosen_model")
        .agg(pl.col("time_run").sum())
    )
    time_.write_csv("results/total_time_final.csv")


def trimmed_mean(df_, cutby=0.2):

    _d = (
        df_.group_by(GROUPING_KEYS)
        .agg(pl.col("prediction_metric").last())
        .group_by(["base_table", "target_dl"])
        .agg(pl.col("prediction_metric").sort())
        .with_columns(len_l=pl.col("prediction_metric").list.len())
        .with_columns(
            start=(pl.col("len_l") * cutby).cast(pl.Int32),
            end=pl.col("len_l") - (pl.col("len_l") * cutby * 2).cast(pl.Int32),
        )
        .with_columns(
            trimmed=(
                pl.col("prediction_metric").list.slice(pl.col("start"), pl.col("end"))
            )
        )
        .with_columns(
            trimmed_mean=pl.col("trimmed").list.mean(),
            trimmed_std=pl.col("trimmed").list.std(),
        )
    )

    return _d


def prepare_reference(df_general):

    dedup = (
        df_general.group_by(GROUPING_KEYS + ["source_table"])
        .agg(pl.col("prediction_metric").mean(), pl.col("time_run").mean())
        .with_columns(base_table=pl.col("source_table"))
    )

    df_reference = dedup.filter(**REFERENCE_CONFIG)
    df_reference.write_csv("results/results_reference.csv")



# %%
df_aggregation = pl.read_parquet("results/results_aggregation.parquet")
df_general = pl.read_parquet("results/results_general.parquet")
df_retrieval = pl.read_parquet("results/results_retrieval.parquet")
df_master = pl.read_parquet("results/master_list.parquet")

# Reformatting time run so that it includes all folds + query time
df_retrieval = prepare_full_time_run(df_retrieval)
df_general = prepare_full_time_run(df_general)
df_aggregation = prepare_full_time_run(df_aggregation)

# %%
# TRIMMED MEAN
df_trimmed = trimmed_mean(df_general, cutby=0.2)
# The table is exported and edited in google sheets for easier formatting
df_trimmed.to_pandas().pivot_table(
    values=["trimmed_mean", "trimmed_std"],
    index="base_table",
    columns="target_dl",
    aggfunc="mean",
).to_csv("results/trimmed_mean.csv")
# fold vs fold difference
# %%
# retrieval method
target = "jd_method"
this_key = [_ for _ in GROUPING_KEYS if _ != target]
this_groupby = [_ for _ in GROUPING_KEYS if not _ in [target, "fold_id"]]
_1 = diff_fold_vs_fold(df_retrieval, this_key)
_1
# %%
# selector
target = "estimator"
this_key = [_ for _ in GROUPING_KEYS if _ != target]
this_groupby = [_ for _ in GROUPING_KEYS if not _ in [target, "fold_id"]]
_2 = diff_fold_vs_fold(df_general, this_key)
_2
# %%
# ml model
target = "chosen_model"
this_key = [_ for _ in GROUPING_KEYS if _ != target]
this_groupby = [_ for _ in GROUPING_KEYS if not _ in [target, "fold_id"]]
_3 = diff_fold_vs_fold(df_general, this_key)
_3


# %%
# aggregation
target = "aggregation"
this_key = [_ for _ in GROUPING_KEYS if _ != target]
this_groupby = [_ for _ in GROUPING_KEYS if not _ in [target, "fold_id"]]
_4 = diff_fold_vs_fold(df_aggregation, this_key)
_4

# %%
# These tables are formatted in google sheets
_1.write_csv("results/diff_from_ref/retrieval_method.csv")
_2.write_csv("results/diff_from_ref/selector.csv")
_3.write_csv("results/diff_from_ref/ml_model.csv")
_4.write_csv("results/diff_from_ref/aggregation.csv")

# %%
