from datetime import datetime

import pandas as pd


def aggregate_actuals_hourly(records: list[dict]) -> pd.DataFrame:
    """Aggregate complete pairs of half-hourly readings into hourly MW."""
    if not records:
        return pd.DataFrame(columns=["delivery_time", "actual_mw"])

    actuals = pd.DataFrame(records).copy()
    actuals["startTime"] = pd.to_datetime(
        actuals["startTime"], utc=True
    )
    actuals["generation"] = pd.to_numeric(
        actuals["generation"], errors="raise"
    )

    if actuals["startTime"].duplicated().any():
        raise ValueError("Duplicate actual-generation timestamps found")

    actuals["delivery_time"] = actuals["startTime"].dt.floor("h")

    hourly = actuals.groupby("delivery_time", as_index=False).agg(
        actual_mw=("generation", "mean"),
        half_hour_count=("generation", "count"),
    )

    minute_offsets = actuals.groupby("delivery_time")["startTime"].apply(
        lambda timestamps: set(timestamps.dt.minute)
    )

    complete_hours = minute_offsets[
        minute_offsets.apply(lambda offsets: offsets == {0, 30})
    ].index

    hourly = hourly[
        (hourly["half_hour_count"] == 2)
        & hourly["delivery_time"].isin(complete_hours)
    ]

    return hourly[["delivery_time", "actual_mw"]].reset_index(drop=True)


def select_forecasts_as_of(
    records: list[dict],
    cutoff: datetime,
) -> pd.DataFrame:
    """Select the latest forecast per delivery hour available at cutoff."""
    if cutoff.tzinfo is None or cutoff.utcoffset() is None:
        raise ValueError("cutoff must include a timezone")

    if not records:
        return pd.DataFrame(columns=["delivery_time", "forecast_mw"])

    forecasts = pd.DataFrame(records).copy()
    forecasts["publishTime"] = pd.to_datetime(
        forecasts["publishTime"], utc=True
    )
    forecasts["startTime"] = pd.to_datetime(
        forecasts["startTime"], utc=True
    )
    forecasts["generation"] = pd.to_numeric(
        forecasts["generation"], errors="raise"
    )

    cutoff_utc = pd.Timestamp(cutoff).tz_convert("UTC")
    eligible = forecasts.loc[
        forecasts["publishTime"] <= cutoff_utc
    ].copy()

    if eligible.empty:
        return pd.DataFrame(columns=["delivery_time", "forecast_mw"])

    eligible = eligible.rename(
        columns={
            "startTime": "delivery_time",
            "generation": "forecast_mw",
        }
    )

    selected = (
        eligible.sort_values("publishTime")
        .drop_duplicates("delivery_time", keep="last")
    )

    return (
        selected[["delivery_time", "forecast_mw"]]
        .sort_values("delivery_time")
        .reset_index(drop=True)
    )


def calculate_errors(
    forecasts: pd.DataFrame,
    actuals: pd.DataFrame,
) -> pd.DataFrame:
    """Align matching hours and calculate forecast minus actual."""
    aligned = forecasts.merge(
        actuals,
        on="delivery_time",
        how="inner",
        validate="one_to_one",
    )

    aligned["error_mw"] = aligned["forecast_mw"] - aligned["actual_mw"]

    return aligned.sort_values("delivery_time").reset_index(drop=True)


def calculate_metrics(
    errors: pd.DataFrame,
) -> dict[str, float | int | None]:
    """Calculate MAE, RMSE, bias, and the number of observations."""
    if errors.empty:
        return {
            "observation_count": 0,
            "mae_mw": None,
            "rmse_mw": None,
            "bias_mw": None,
        }

    values = errors["error_mw"]

    return {
        "observation_count": len(values),
        "mae_mw": float(values.abs().mean()),
        "rmse_mw": float((values.pow(2).mean()) ** 0.5),
        "bias_mw": float(values.mean()),
    }


def inspect_data_availability(
    actual_records: list[dict],
    forecast_records: list[dict],
    cutoff: datetime,
) -> dict[str, int]:
    """Summarize usable actual, forecast, and aligned observations."""

    actuals = aggregate_actuals_hourly(actual_records)

    forecasts = select_forecasts_as_of(
        forecast_records,
        cutoff,
    )

    errors = calculate_errors(forecasts, actuals)

    return {
        "actual_hours_available": len(actuals),
        "forecast_hours_available": len(forecasts),
        "evaluated_hours": len(errors),
    }
