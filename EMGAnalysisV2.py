"""
=======================================================================
TIME-NORMALISED GAIT-CYCLE EMG ANALYSIS
=======================================================================

Conditions:
1. No exosuit
2. Exosuit off / no actuation
3. Exosuit on - constant assistance
4. Exosuit on - variable assistance

Outputs:
- Mean ± one standard deviation gait-cycle EMG figure
- Median activation figure
- Normalised median activation figure
- Heel-strike diagnostic plots
- Excel summary tables
- CSV files containing mean and SD profiles
- Individual gait-cycle metrics

Required packages:
    python3 -m pip install numpy pandas scipy matplotlib openpyxl

=======================================================================
"""

from __future__ import annotations

import re
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import (
    butter,
    filtfilt,
    find_peaks,
    iirnotch,
    sosfiltfilt,
)

warnings.filterwarnings("ignore", category=RuntimeWarning)


# =====================================================================
# USER SETTINGS
# =====================================================================

BASE_FOLDER = Path(__file__).resolve().parent

OUTPUT_FOLDER = BASE_FOLDER / "Tianyu_Gait_Cycle_EMG_Analysis"


# ---------------------------------------------------------------------
# EMG FILES
# ---------------------------------------------------------------------

EMG_FILES = {
    "No exosuit": BASE_FOLDER / "Tianyu_nosuitWalking.xlsx",

    "Exosuit off": (
        BASE_FOLDER / "Tianyu_withsuitWalking_noActuation.xlsx"
    ),

    "Exosuit on - constant": (
        BASE_FOLDER / "Tianyu_suitWalkingConstantActuation.xlsx"
    ),

    "Exosuit on - variable": (
        BASE_FOLDER / "Tianyu_suitWalkingVariableActuation.xlsx"
    ),
}


# ---------------------------------------------------------------------
# GAIT FILES
# ---------------------------------------------------------------------

GAIT_FILES = {
    "No exosuit": BASE_FOLDER / "TianyuWithoutExo.csv",

    "Exosuit off": (
        BASE_FOLDER / "TianyuWithExo_noAssistance.csv"
    ),

    "Exosuit on - constant": (
        BASE_FOLDER / "TianyuWalking_constantAssistance.csv"
    ),

    "Exosuit on - variable": (
        BASE_FOLDER / "TianyuVariableWalking.csv"
    ),
}


# ---------------------------------------------------------------------
# MANUAL EMG–GAIT TIME OFFSETS
# ---------------------------------------------------------------------
#
# The EMG and gait recording systems may not start at exactly the same
# moment.
#
# The corrected EMG time is:
#
#     corrected_emg_time = emg_time + offset
#
# Examples:
#
# If EMG started 1.5 seconds AFTER gait recording:
#     offset = 1.5
#
# If EMG started 1.5 seconds BEFORE gait recording:
#     offset = -1.5
#
# Start with zero and inspect the generated figures.
#

EMG_TIME_OFFSETS_SECONDS = {
    "No exosuit": 0.0,
    "Exosuit off": 0.0,
    "Exosuit on - constant": 0.0,
    "Exosuit on - variable": 0.0,
}


# ---------------------------------------------------------------------
# EMG PROCESSING
# ---------------------------------------------------------------------

POWER_LINE_FREQUENCY_HZ = 50.0

BANDPASS_LOW_HZ = 20.0
BANDPASS_HIGH_HZ = 450.0
BANDPASS_ORDER = 4

ENVELOPE_LOW_PASS_HZ = 6.0
ENVELOPE_FILTER_ORDER = 4

NOTCH_QUALITY_FACTOR = 30.0

NUMBER_OF_GAIT_POINTS = 101

MINIMUM_GAIT_CYCLE_SECONDS = 0.50
MAXIMUM_GAIT_CYCLE_SECONDS = 2.50

MINIMUM_CYCLE_COVERAGE = 0.95

# Ignore possible unstable cycles at beginning and end.
NUMBER_OF_INITIAL_CYCLES_TO_REMOVE = 1
NUMBER_OF_FINAL_CYCLES_TO_REMOVE = 1


# ---------------------------------------------------------------------
# MEDIAN ACTIVATION WINDOW
# ---------------------------------------------------------------------
#
# Median activation is calculated over the full gait cycle by default.
#
# To calculate it over a specific region, such as 80–100%, change:
#
# MEDIAN_WINDOW_START_PERCENT = 80
# MEDIAN_WINDOW_END_PERCENT = 100
#

MEDIAN_WINDOW_START_PERCENT = 0
MEDIAN_WINDOW_END_PERCENT = 100


# ---------------------------------------------------------------------
# MUSCLE CHANNELS
# ---------------------------------------------------------------------

EMG_COLUMNS = {
    "RF": "RF: EMG 1 [Volts]",
    "VM": "VM: EMG 2 [Volts]",
    "VL": "VL: EMG 3 [Volts]",
    "BF": "BF: EMG 4 [Volts]",
    "TA": "TA: EMG 5 [Volts]",
    "GM": "GM: EMG 6 [Volts]",
}

MUSCLE_TITLES = {
    "RF": "Rectus Femoris",
    "VM": "Vastus Medialis",
    "VL": "Vastus Lateralis",
    "BF": "Biceps Femoris",
    "TA": "Tibialis Anterior",
    "GM": "Gastrocnemius Medialis",
}


# =====================================================================
# GENERAL UTILITY FUNCTIONS
# =====================================================================

def clean_column_name(column_name: object) -> str:
    """Return a clean single-line column name."""

    text = str(column_name)

    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_dataframe_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Clean all dataframe column names."""

    dataframe = dataframe.copy()

    dataframe.columns = [
        clean_column_name(column)
        for column in dataframe.columns
    ]

    return dataframe


def convert_to_numeric(series: pd.Series) -> pd.Series:
    """Safely convert a pandas series to numeric values."""

    return pd.to_numeric(
        series,
        errors="coerce",
    )


def ensure_file_exists(file_path: Path) -> None:
    """Raise a helpful error when an input file does not exist."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"\nInput file was not found:\n"
            f"{file_path}\n\n"
            f"Check the filename and file location."
        )


# =====================================================================
# FILE READING
# =====================================================================

def read_emg_excel(file_path: Path) -> pd.DataFrame:
    """
    Read the EMG Excel file.

    Pandas automatically renames duplicate time columns:
        X [s]
        X [s].1
        X [s].2
        etc.

    The first X [s] column is used as the common EMG time.
    """

    ensure_file_exists(file_path)

    dataframe = pd.read_excel(
        file_path,
        sheet_name=0,
        engine="openpyxl",
    )

    dataframe = clean_dataframe_columns(dataframe)

    return dataframe


def read_gait_csv(file_path: Path) -> pd.DataFrame:
    """
    Read a gait file robustly.

    It first attempts automatic delimiter detection, then tab-separated,
    then comma-separated reading.
    """

    ensure_file_exists(file_path)

    reading_errors = []

    reading_methods = [
        {
            "sep": None,
            "engine": "python",
        },
        {
            "sep": "\t",
            "engine": "python",
        },
        {
            "sep": ",",
            "engine": "python",
        },
    ]

    for method in reading_methods:

        try:
            dataframe = pd.read_csv(
                file_path,
                **method,
            )

            dataframe = clean_dataframe_columns(dataframe)

            if len(dataframe.columns) > 2:
                return dataframe

        except Exception as error:
            reading_errors.append(str(error))

    raise ValueError(
        f"Unable to read gait file:\n{file_path}\n\n"
        f"Errors:\n" + "\n".join(reading_errors)
    )


# =====================================================================
# EMG TIME AND SIGNAL EXTRACTION
# =====================================================================

def find_first_emg_time_column(
    dataframe: pd.DataFrame,
) -> str:
    """
    Find the first EMG time column.

    It accepts:
        X [s]
        X [s].1
        X [s].2
    """

    for column in dataframe.columns:

        normalised = column.lower().replace(" ", "")

        if normalised.startswith("x[s]"):
            return column

    raise KeyError(
        "No EMG time column beginning with 'X [s]' was found."
    )


def extract_emg_data(
    dataframe: pd.DataFrame,
) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
    """
    Extract time and the six EMG channels.
    """

    time_column = find_first_emg_time_column(dataframe)

    required_columns = list(EMG_COLUMNS.values())

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise KeyError(
            "The following EMG columns were not found:\n"
            + "\n".join(missing_columns)
            + "\n\nAvailable columns:\n"
            + "\n".join(dataframe.columns)
        )

    extracted = pd.DataFrame()

    extracted["Time"] = convert_to_numeric(
        dataframe[time_column]
    )

    for muscle, column_name in EMG_COLUMNS.items():
        extracted[muscle] = convert_to_numeric(
            dataframe[column_name]
        )

    extracted = extracted.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    extracted = extracted.dropna(
        subset=["Time"],
    )

    extracted = extracted.sort_values("Time")

    extracted = extracted.drop_duplicates(
        subset=["Time"],
        keep="first",
    )

    # Interpolate occasional missing EMG values.
    for muscle in EMG_COLUMNS:
        extracted[muscle] = (
            extracted[muscle]
            .interpolate(limit_direction="both")
        )

    extracted = extracted.dropna()

    time = extracted["Time"].to_numpy(dtype=float)

    # Convert time to relative time beginning at zero.
    time = time - time[0]

    emg_signals = {
        muscle: extracted[muscle].to_numpy(dtype=float)
        for muscle in EMG_COLUMNS
    }

    return time, emg_signals


def estimate_sampling_frequency(
    time: np.ndarray,
) -> float:
    """Estimate EMG sampling frequency from the time vector."""

    time_difference = np.diff(time)

    valid_difference = time_difference[
        np.isfinite(time_difference)
        & (time_difference > 0)
    ]

    if len(valid_difference) == 0:
        raise ValueError(
            "Unable to estimate EMG sampling frequency."
        )

    median_dt = float(np.median(valid_difference))

    sampling_frequency = 1.0 / median_dt

    return sampling_frequency


# =====================================================================
# EMG FILTERING
# =====================================================================

def remove_dc_offset(signal: np.ndarray) -> np.ndarray:
    """Remove the signal mean."""

    return signal - np.nanmean(signal)


def apply_notch_filter(
    signal: np.ndarray,
    sampling_frequency: float,
) -> np.ndarray:
    """Apply a 50 Hz notch filter."""

    nyquist_frequency = sampling_frequency / 2.0

    if POWER_LINE_FREQUENCY_HZ >= nyquist_frequency:
        return signal.copy()

    normalised_frequency = (
        POWER_LINE_FREQUENCY_HZ / nyquist_frequency
    )

    b_notch, a_notch = iirnotch(
        normalised_frequency,
        NOTCH_QUALITY_FACTOR,
    )

    return filtfilt(
        b_notch,
        a_notch,
        signal,
    )


def apply_bandpass_filter(
    signal: np.ndarray,
    sampling_frequency: float,
) -> np.ndarray:
    """Apply the EMG band-pass filter."""

    nyquist_frequency = sampling_frequency / 2.0

    low_frequency = BANDPASS_LOW_HZ

    # Prevent upper cutoff from exceeding Nyquist.
    high_frequency = min(
        BANDPASS_HIGH_HZ,
        nyquist_frequency * 0.95,
    )

    if high_frequency <= low_frequency:
        raise ValueError(
            f"Sampling frequency is too low for the requested "
            f"band-pass filter.\n"
            f"Sampling frequency: {sampling_frequency:.2f} Hz\n"
            f"Requested lower cutoff: {low_frequency:.2f} Hz"
        )

    sos = butter(
        BANDPASS_ORDER,
        [
            low_frequency / nyquist_frequency,
            high_frequency / nyquist_frequency,
        ],
        btype="bandpass",
        output="sos",
    )

    return sosfiltfilt(
        sos,
        signal,
    )


def calculate_linear_envelope(
    rectified_signal: np.ndarray,
    sampling_frequency: float,
) -> np.ndarray:
    """Create a low-pass-filtered linear EMG envelope."""

    nyquist_frequency = sampling_frequency / 2.0

    cutoff_frequency = min(
        ENVELOPE_LOW_PASS_HZ,
        nyquist_frequency * 0.90,
    )

    sos = butter(
        ENVELOPE_FILTER_ORDER,
        cutoff_frequency / nyquist_frequency,
        btype="lowpass",
        output="sos",
    )

    envelope = sosfiltfilt(
        sos,
        rectified_signal,
    )

    # Numerical filtering can create tiny negative values.
    envelope = np.maximum(envelope, 0.0)

    return envelope


def process_emg_signal(
    raw_signal: np.ndarray,
    sampling_frequency: float,
) -> Dict[str, np.ndarray]:
    """
    Complete EMG processing pipeline.
    """

    dc_removed = remove_dc_offset(raw_signal)

    notched = apply_notch_filter(
        dc_removed,
        sampling_frequency,
    )

    bandpassed = apply_bandpass_filter(
        notched,
        sampling_frequency,
    )

    rectified = np.abs(bandpassed)

    envelope = calculate_linear_envelope(
        rectified,
        sampling_frequency,
    )

    return {
        "Raw": raw_signal,
        "DC removed": dc_removed,
        "Notched": notched,
        "Bandpassed": bandpassed,
        "Rectified": rectified,
        "Envelope": envelope,
    }


# =====================================================================
# GAIT DATA AND HEEL-STRIKE DETECTION
# =====================================================================

def extract_gait_time(
    dataframe: pd.DataFrame,
) -> np.ndarray:
    """Extract and clean the gait time vector."""

    if "Time" not in dataframe.columns:
        raise KeyError(
            "The gait file does not contain a 'Time' column."
        )

    gait_time = convert_to_numeric(
        dataframe["Time"]
    ).to_numpy(dtype=float)

    valid = np.isfinite(gait_time)

    gait_time = gait_time[valid]

    gait_time = gait_time - gait_time[0]

    return gait_time


def binary_rising_edges(
    signal: np.ndarray,
    threshold: float,
) -> np.ndarray:
    """Return indices where a thresholded signal rises from 0 to 1."""

    binary_signal = (
        np.asarray(signal, dtype=float) > threshold
    ).astype(int)

    rising_edges = np.where(
        np.diff(binary_signal, prepend=0) == 1
    )[0]

    return rising_edges


def remove_events_too_close(
    event_times: np.ndarray,
    minimum_separation_seconds: float = 0.35,
) -> np.ndarray:
    """Remove repeated heel-strike events occurring too close together."""

    event_times = np.asarray(
        event_times,
        dtype=float,
    )

    event_times = event_times[
        np.isfinite(event_times)
    ]

    event_times = np.sort(event_times)

    if len(event_times) == 0:
        return event_times

    accepted_events = [event_times[0]]

    for event_time in event_times[1:]:

        if (
            event_time - accepted_events[-1]
            >= minimum_separation_seconds
        ):
            accepted_events.append(event_time)

    return np.asarray(
        accepted_events,
        dtype=float,
    )


def evaluate_heel_strikes(
    heel_strikes: np.ndarray,
) -> float:
    """
    Give a quality score to a candidate heel-strike sequence.

    Higher score means more plausible walking-cycle timing.
    """

    if len(heel_strikes) < 3:
        return -np.inf

    intervals = np.diff(heel_strikes)

    valid_intervals = intervals[
        (intervals >= MINIMUM_GAIT_CYCLE_SECONDS)
        & (intervals <= MAXIMUM_GAIT_CYCLE_SECONDS)
    ]

    if len(valid_intervals) == 0:
        return -np.inf

    valid_fraction = (
        len(valid_intervals) / len(intervals)
    )

    interval_variability = (
        np.std(valid_intervals)
        / max(np.mean(valid_intervals), 1e-9)
    )

    score = (
        10.0 * valid_fraction
        + 0.1 * len(valid_intervals)
        - interval_variability
    )

    return float(score)


def detect_from_pulse_column(
    dataframe: pd.DataFrame,
    gait_time: np.ndarray,
    column_name: str,
) -> Optional[np.ndarray]:
    """Detect heel strikes from a pulse/binary column."""

    if column_name not in dataframe.columns:
        return None

    signal = convert_to_numeric(
        dataframe[column_name]
    ).to_numpy(dtype=float)

    length = min(
        len(signal),
        len(gait_time),
    )

    signal = signal[:length]
    time = gait_time[:length]

    finite_signal = signal[
        np.isfinite(signal)
    ]

    if len(finite_signal) == 0:
        return None

    minimum = np.nanpercentile(
        finite_signal,
        5,
    )

    maximum = np.nanpercentile(
        finite_signal,
        95,
    )

    if maximum == minimum:
        return None

    threshold = minimum + 0.5 * (
        maximum - minimum
    )

    indices = binary_rising_edges(
        signal,
        threshold,
    )

    heel_strikes = time[indices]

    heel_strikes = remove_events_too_close(
        heel_strikes,
    )

    return heel_strikes


def detect_from_fsr_column(
    dataframe: pd.DataFrame,
    gait_time: np.ndarray,
    column_name: str,
) -> Optional[np.ndarray]:
    """
    Detect heel strikes from an analogue heel FSR.

    Both high-contact and low-contact conventions are evaluated.
    """

    if column_name not in dataframe.columns:
        return None

    signal = convert_to_numeric(
        dataframe[column_name]
    ).to_numpy(dtype=float)

    length = min(
        len(signal),
        len(gait_time),
    )

    signal = signal[:length]
    time = gait_time[:length]

    valid_mask = np.isfinite(signal)

    if np.sum(valid_mask) < 10:
        return None

    signal_series = pd.Series(signal)

    signal = (
        signal_series
        .interpolate(limit_direction="both")
        .to_numpy(dtype=float)
    )

    low_value = np.nanpercentile(
        signal,
        15,
    )

    high_value = np.nanpercentile(
        signal,
        85,
    )

    threshold = (
        low_value + high_value
    ) / 2.0

    # Candidate 1: contact produces a high signal.
    high_contact_indices = binary_rising_edges(
        signal,
        threshold,
    )

    high_contact_times = remove_events_too_close(
        time[high_contact_indices]
    )

    # Candidate 2: contact produces a low signal.
    low_contact_indices = binary_rising_edges(
        -signal,
        -threshold,
    )

    low_contact_times = remove_events_too_close(
        time[low_contact_indices]
    )

    high_score = evaluate_heel_strikes(
        high_contact_times
    )

    low_score = evaluate_heel_strikes(
        low_contact_times
    )

    if high_score >= low_score:
        return high_contact_times

    return low_contact_times


def detect_right_heel_strikes(
    gait_dataframe: pd.DataFrame,
) -> Tuple[np.ndarray, str]:
    """
    Detect right heel strikes.

    Preferred order:
        1. HeelRp
        2. heelR
        3. FSR R Heel

    All available candidates are evaluated and the best plausible
    sequence is selected.
    """

    gait_dataframe = gait_dataframe.copy()

    gait_dataframe = gait_dataframe.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    gait_dataframe["Time"] = convert_to_numeric(
        gait_dataframe["Time"]
    )

    gait_dataframe = gait_dataframe.dropna(
        subset=["Time"],
    )

    gait_dataframe = gait_dataframe.sort_values(
        "Time"
    )

    gait_dataframe = gait_dataframe.drop_duplicates(
        subset=["Time"],
        keep="first",
    )

    gait_time = (
        gait_dataframe["Time"].to_numpy(dtype=float)
    )

    gait_time = gait_time - gait_time[0]

    candidates: List[
        Tuple[str, np.ndarray, float]
    ] = []

    pulse_columns = [
        "HeelRp",
        "heelR",
    ]

    for column_name in pulse_columns:

        detected = detect_from_pulse_column(
            gait_dataframe,
            gait_time,
            column_name,
        )

        if detected is not None:

            score = evaluate_heel_strikes(
                detected
            )

            candidates.append(
                (
                    column_name,
                    detected,
                    score,
                )
            )

    detected_fsr = detect_from_fsr_column(
        gait_dataframe,
        gait_time,
        "FSR R Heel",
    )

    if detected_fsr is not None:

        score = evaluate_heel_strikes(
            detected_fsr
        )

        candidates.append(
            (
                "FSR R Heel",
                detected_fsr,
                score,
            )
        )

    valid_candidates = [
        candidate
        for candidate in candidates
        if np.isfinite(candidate[2])
    ]

    if not valid_candidates:
        raise RuntimeError(
            "No reliable right heel strikes could be detected from "
            "'HeelRp', 'heelR', or 'FSR R Heel'."
        )

    valid_candidates.sort(
        key=lambda item: item[2],
        reverse=True,
    )

    selected_name, heel_strikes, selected_score = (
        valid_candidates[0]
    )

    print(
        f"  Selected heel-strike signal: {selected_name}"
    )

    print(
        f"  Detected right heel strikes: {len(heel_strikes)}"
    )

    if len(heel_strikes) >= 2:

        gait_periods = np.diff(heel_strikes)

        valid_periods = gait_periods[
            (
                gait_periods
                >= MINIMUM_GAIT_CYCLE_SECONDS
            )
            & (
                gait_periods
                <= MAXIMUM_GAIT_CYCLE_SECONDS
            )
        ]

        if len(valid_periods) > 0:
            print(
                f"  Median right gait-cycle duration: "
                f"{np.median(valid_periods):.3f} s"
            )

    return heel_strikes, selected_name


# =====================================================================
# GAIT-CYCLE SEGMENTATION
# =====================================================================

def prepare_valid_gait_intervals(
    heel_strikes: np.ndarray,
) -> List[Tuple[float, float]]:
    """Create valid right gait-cycle intervals."""

    intervals: List[
        Tuple[float, float]
    ] = []

    for cycle_index in range(
        len(heel_strikes) - 1
    ):

        start_time = float(
            heel_strikes[cycle_index]
        )

        end_time = float(
            heel_strikes[cycle_index + 1]
        )

        duration = end_time - start_time

        if (
            MINIMUM_GAIT_CYCLE_SECONDS
            <= duration
            <= MAXIMUM_GAIT_CYCLE_SECONDS
        ):
            intervals.append(
                (
                    start_time,
                    end_time,
                )
            )

    if (
        NUMBER_OF_INITIAL_CYCLES_TO_REMOVE > 0
        and len(intervals)
        > NUMBER_OF_INITIAL_CYCLES_TO_REMOVE
    ):
        intervals = intervals[
            NUMBER_OF_INITIAL_CYCLES_TO_REMOVE:
        ]

    if (
        NUMBER_OF_FINAL_CYCLES_TO_REMOVE > 0
        and len(intervals)
        > NUMBER_OF_FINAL_CYCLES_TO_REMOVE
    ):
        intervals = intervals[
            :-NUMBER_OF_FINAL_CYCLES_TO_REMOVE
        ]

    return intervals


def time_normalise_cycle(
    signal_time: np.ndarray,
    signal: np.ndarray,
    cycle_start_time: float,
    cycle_end_time: float,
) -> Optional[np.ndarray]:
    """
    Extract one gait cycle and interpolate it to 101 points.
    """

    cycle_duration = (
        cycle_end_time - cycle_start_time
    )

    target_time = np.linspace(
        cycle_start_time,
        cycle_end_time,
        NUMBER_OF_GAIT_POINTS,
    )

    available_start = max(
        cycle_start_time,
        signal_time[0],
    )

    available_end = min(
        cycle_end_time,
        signal_time[-1],
    )

    available_duration = (
        available_end - available_start
    )

    coverage = (
        available_duration / cycle_duration
    )

    if coverage < MINIMUM_CYCLE_COVERAGE:
        return None

    cycle_mask = (
        (signal_time >= cycle_start_time)
        & (signal_time <= cycle_end_time)
    )

    if np.sum(cycle_mask) < 5:
        return None

    cycle_time = signal_time[cycle_mask]
    cycle_signal = signal[cycle_mask]

    finite_mask = (
        np.isfinite(cycle_time)
        & np.isfinite(cycle_signal)
    )

    cycle_time = cycle_time[finite_mask]
    cycle_signal = cycle_signal[finite_mask]

    if len(cycle_time) < 5:
        return None

    normalised_cycle = np.interp(
        target_time,
        cycle_time,
        cycle_signal,
    )

    return normalised_cycle


def segment_emg_into_cycles(
    corrected_emg_time: np.ndarray,
    processed_envelopes: Dict[str, np.ndarray],
    gait_intervals: List[Tuple[float, float]],
    condition: str,
) -> Tuple[
    Dict[str, np.ndarray],
    pd.DataFrame,
]:
    """
    Segment all six muscles into right gait cycles.
    """

    cycles_by_muscle: Dict[
        str,
        List[np.ndarray]
    ] = {
        muscle: []
        for muscle in EMG_COLUMNS
    }

    cycle_metric_rows = []

    for cycle_number, (
        cycle_start,
        cycle_end,
    ) in enumerate(
        gait_intervals,
        start=1,
    ):

        duration = cycle_end - cycle_start

        normalised_cycles_for_current_cycle = {}

        valid_for_all_muscles = True

        for muscle in EMG_COLUMNS:

            normalised_cycle = time_normalise_cycle(
                corrected_emg_time,
                processed_envelopes[muscle],
                cycle_start,
                cycle_end,
            )

            if normalised_cycle is None:
                valid_for_all_muscles = False
                break

            normalised_cycles_for_current_cycle[
                muscle
            ] = normalised_cycle

        # Use only cycles that are valid for every muscle.
        if not valid_for_all_muscles:
            continue

        for muscle, normalised_cycle in (
            normalised_cycles_for_current_cycle.items()
        ):

            cycles_by_muscle[muscle].append(
                normalised_cycle
            )

            gait_percent = np.linspace(
                0,
                100,
                NUMBER_OF_GAIT_POINTS,
            )

            median_mask = (
                (
                    gait_percent
                    >= MEDIAN_WINDOW_START_PERCENT
                )
                & (
                    gait_percent
                    <= MEDIAN_WINDOW_END_PERCENT
                )
            )

            median_activation = float(
                np.median(
                    normalised_cycle[median_mask]
                )
            )

            mean_activation = float(
                np.mean(
                    normalised_cycle[median_mask]
                )
            )

            rms_activation = float(
                np.sqrt(
                    np.mean(
                        normalised_cycle[
                            median_mask
                        ] ** 2
                    )
                )
            )

            integrated_activation = float(
                     np.trapezoid(
                     normalised_cycle[median_mask],
                      gait_percent[median_mask],
                         )
                    )

            cycle_metric_rows.append(
                {
                    "Condition": condition,
                    "Cycle number": cycle_number,
                    "Cycle start time (s)": (
                        cycle_start
                    ),
                    "Cycle end time (s)": (
                        cycle_end
                    ),
                    "Cycle duration (s)": duration,
                    "Muscle": muscle,
                    "Muscle name": (
                        MUSCLE_TITLES[muscle]
                    ),
                    "Median activation (V)": (
                        median_activation
                    ),
                    "Mean activation (V)": (
                        mean_activation
                    ),
                    "RMS envelope (V)": (
                        rms_activation
                    ),
                    "Integrated envelope "
                    "(V.% gait)": (
                        integrated_activation
                    ),
                    "Analysis window start (%)": (
                        MEDIAN_WINDOW_START_PERCENT
                    ),
                    "Analysis window end (%)": (
                        MEDIAN_WINDOW_END_PERCENT
                    ),
                }
            )

    cycle_arrays = {}

    for muscle, cycle_list in (
        cycles_by_muscle.items()
    ):

        if len(cycle_list) == 0:
            cycle_arrays[muscle] = np.empty(
                (
                    0,
                    NUMBER_OF_GAIT_POINTS,
                )
            )
        else:
            cycle_arrays[muscle] = np.vstack(
                cycle_list
            )

    cycle_metrics = pd.DataFrame(
        cycle_metric_rows
    )

    return cycle_arrays, cycle_metrics


# =====================================================================
# CONDITION PROCESSING
# =====================================================================

def process_condition(
    condition: str,
    emg_file: Path,
    gait_file: Path,
) -> Dict[str, object]:
    """Process one experimental condition."""

    print("\n" + "=" * 78)
    print(f"Condition: {condition}")
    print("=" * 78)

    print(f"EMG file:  {emg_file.name}")
    print(f"Gait file: {gait_file.name}")

    emg_dataframe = read_emg_excel(
        emg_file
    )

    gait_dataframe = read_gait_csv(
        gait_file
    )

    emg_time, raw_emg = extract_emg_data(
        emg_dataframe
    )

    sampling_frequency = estimate_sampling_frequency(
        emg_time
    )

    print(
        f"  Estimated EMG sampling frequency: "
        f"{sampling_frequency:.2f} Hz"
    )

    corrected_emg_time = (
        emg_time
        + EMG_TIME_OFFSETS_SECONDS[condition]
    )

    processed_envelopes = {}

    processed_signals = {}

    for muscle, raw_signal in raw_emg.items():

        processing_result = process_emg_signal(
            raw_signal,
            sampling_frequency,
        )

        processed_signals[muscle] = (
            processing_result
        )

        processed_envelopes[muscle] = (
            processing_result["Envelope"]
        )

    heel_strikes, heel_source = (
        detect_right_heel_strikes(
            gait_dataframe
        )
    )

    gait_intervals = (
        prepare_valid_gait_intervals(
            heel_strikes
        )
    )

    print(
        f"  Valid gait intervals after filtering: "
        f"{len(gait_intervals)}"
    )

    cycle_arrays, cycle_metrics = (
        segment_emg_into_cycles(
            corrected_emg_time,
            processed_envelopes,
            gait_intervals,
            condition,
        )
    )

    number_of_cycles = min(
        cycle_arrays[muscle].shape[0]
        for muscle in EMG_COLUMNS
    )

    print(
        f"  Gait cycles used in EMG analysis: "
        f"{number_of_cycles}"
    )

    if number_of_cycles == 0:
        raise RuntimeError(
            f"No EMG gait cycles were obtained for "
            f"{condition}.\n"
            f"The likely cause is an EMG–gait time alignment "
            f"problem.\n"
            f"Adjust EMG_TIME_OFFSETS_SECONDS for this "
            f"condition."
        )

    return {
        "Condition": condition,
        "EMG time": corrected_emg_time,
        "Raw EMG": raw_emg,
        "Processed signals": processed_signals,
        "Envelopes": processed_envelopes,
        "Sampling frequency": sampling_frequency,
        "Heel strikes": heel_strikes,
        "Heel source": heel_source,
        "Gait intervals": gait_intervals,
        "Cycles": cycle_arrays,
        "Cycle metrics": cycle_metrics,
        "Number of cycles": number_of_cycles,
    }


# =====================================================================
# PROFILE CALCULATIONS
# =====================================================================

def calculate_condition_profiles(
    all_results: Dict[str, Dict[str, object]],
) -> Tuple[
    Dict[str, Dict[str, Dict[str, np.ndarray]]],
    pd.DataFrame,
]:
    """Calculate mean, SD and median profiles."""

    gait_percent = np.linspace(
        0,
        100,
        NUMBER_OF_GAIT_POINTS,
    )

    profiles = {}

    profile_rows = []

    for condition, result in all_results.items():

        profiles[condition] = {}

        for muscle in EMG_COLUMNS:

            cycles = result["Cycles"][muscle]

            mean_profile = np.mean(
                cycles,
                axis=0,
            )

            standard_deviation_profile = np.std(
                cycles,
                axis=0,
                ddof=1 if cycles.shape[0] > 1 else 0,
            )

            median_profile = np.median(
                cycles,
                axis=0,
            )

            q25_profile = np.percentile(
                cycles,
                25,
                axis=0,
            )

            q75_profile = np.percentile(
                cycles,
                75,
                axis=0,
            )

            profiles[condition][muscle] = {
                "Mean": mean_profile,
                "SD": standard_deviation_profile,
                "Median": median_profile,
                "Q25": q25_profile,
                "Q75": q75_profile,
            }

            for point_index, percent in enumerate(
                gait_percent
            ):

                profile_rows.append(
                    {
                        "Condition": condition,
                        "Muscle": muscle,
                        "Muscle name": (
                            MUSCLE_TITLES[muscle]
                        ),
                        "Gait cycle (%)": percent,
                        "Mean envelope (V)": (
                            mean_profile[point_index]
                        ),
                        "SD envelope (V)": (
                            standard_deviation_profile[
                                point_index
                            ]
                        ),
                        "Median envelope (V)": (
                            median_profile[
                                point_index
                            ]
                        ),
                        "25th percentile (V)": (
                            q25_profile[point_index]
                        ),
                        "75th percentile (V)": (
                            q75_profile[point_index]
                        ),
                        "Number of cycles": (
                            cycles.shape[0]
                        ),
                    }
                )

    profile_dataframe = pd.DataFrame(
        profile_rows
    )

    return profiles, profile_dataframe


# =====================================================================
# MEDIAN ACTIVATION SUMMARY
# =====================================================================

def create_median_summary(
    all_cycle_metrics: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Summarise cycle-level median activation.

    The condition median is the median of the individual cycle medians.
    """

    summary = (
        all_cycle_metrics
        .groupby(
            [
                "Condition",
                "Muscle",
                "Muscle name",
            ],
            as_index=False,
        )
        .agg(
            Number_of_cycles=(
                "Median activation (V)",
                "count",
            ),
            Median_activation_V=(
                "Median activation (V)",
                "median",
            ),
            Mean_of_cycle_medians_V=(
                "Median activation (V)",
                "mean",
            ),
            SD_of_cycle_medians_V=(
                "Median activation (V)",
                "std",
            ),
            Q25_cycle_median_V=(
                "Median activation (V)",
                lambda values: np.percentile(
                    values,
                    25,
                ),
            ),
            Q75_cycle_median_V=(
                "Median activation (V)",
                lambda values: np.percentile(
                    values,
                    75,
                ),
            ),
        )
    )

    baseline = (
        summary[
            summary["Condition"] == "No exosuit"
        ][
            [
                "Muscle",
                "Median_activation_V",
            ]
        ]
        .rename(
            columns={
                "Median_activation_V":
                "No_exosuit_median_V",
            }
        )
    )

    normalised_summary = summary.merge(
        baseline,
        on="Muscle",
        how="left",
    )

    normalised_summary[
        "Normalised median activation (%)"
    ] = (
        normalised_summary[
            "Median_activation_V"
        ]
        / normalised_summary[
            "No_exosuit_median_V"
        ]
        * 100.0
    )

    normalised_summary[
        "Change from no exosuit (%)"
    ] = (
        normalised_summary[
            "Normalised median activation (%)"
        ]
        - 100.0
    )

    return summary, normalised_summary


# =====================================================================
# PLOTTING
# =====================================================================

def plot_mean_sd_profiles(
    profiles: Dict[
        str,
        Dict[
            str,
            Dict[str, np.ndarray],
        ],
    ],
    all_results: Dict[str, Dict[str, object]],
    output_folder: Path,
) -> None:
    """
    Plot mean ± one standard deviation, matching the requested layout.
    """

    gait_percent = np.linspace(
        0,
        100,
        NUMBER_OF_GAIT_POINTS,
    )

    conditions = list(
        EMG_FILES.keys()
    )

    condition_labels = {
        "No exosuit": "No exosuit",
        "Exosuit off": "Exosuit off",
        "Exosuit on - constant": (
            "Exosuit on - constant"
        ),
        "Exosuit on - variable": (
            "Exosuit on - variable"
        ),
    }

    muscle_order = [
        "RF",
        "VM",
        "VL",
        "BF",
        "TA",
        "GM",
    ]

    figure, axes = plt.subplots(
        3,
        2,
        figsize=(16, 9),
        sharex=True,
    )

    axes = axes.flatten()

    for axis, muscle in zip(
        axes,
        muscle_order,
    ):

        for condition in conditions:

            mean_profile = (
                profiles[condition][muscle]["Mean"]
            )

            sd_profile = (
                profiles[condition][muscle]["SD"]
            )

            line = axis.plot(
                gait_percent,
                mean_profile,
                linewidth=2.0,
                label=condition_labels[condition],
            )[0]

            axis.fill_between(
                gait_percent,
                mean_profile - sd_profile,
                mean_profile + sd_profile,
                alpha=0.14,
                color=line.get_color(),
                linewidth=0,
            )

        axis.set_title(
            MUSCLE_TITLES[muscle],
            fontsize=13,
            fontweight="bold",
        )

        axis.set_xlim(
            0,
            100,
        )

        axis.set_xlabel(
            "Right gait cycle (%)",
            fontsize=11,
        )

        axis.set_ylabel(
            "Processed EMG (V)",
            fontsize=11,
        )

        axis.grid(
            True,
            alpha=0.3,
        )

        axis.ticklabel_format(
            axis="y",
            style="sci",
            scilimits=(-3, 3),
        )

    cycle_text = ", ".join(
        [
            (
                f"{condition}: "
                f"{all_results[condition]['Number of cycles']}"
            )
            for condition in conditions
        ]
    )

    figure.suptitle(
        "Time-normalised right gait-cycle EMG: Tianyu\n"
        "Mean ± one standard deviation across gait cycles",
        fontsize=17,
        fontweight="bold",
        y=0.995,
    )

    handles, labels = axes[0].get_legend_handles_labels()

    figure.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.945),
        ncol=4,
        frameon=False,
        fontsize=10,
    )

    figure.text(
        0.5,
        0.012,
        f"Number of accepted cycles — {cycle_text}",
        ha="center",
        fontsize=9,
    )

    figure.tight_layout(
        rect=[
            0.02,
            0.04,
            0.99,
            0.90,
        ]
    )

    figure.savefig(
        output_folder
        / "Mean_SD_Time_Normalised_Right_Gait_EMG.png",
        dpi=300,
        bbox_inches="tight",
    )

    figure.savefig(
        output_folder
        / "Mean_SD_Time_Normalised_Right_Gait_EMG.pdf",
        bbox_inches="tight",
    )

    plt.close(figure)


def plot_median_iqr_profiles(
    profiles: Dict[
        str,
        Dict[
            str,
            Dict[str, np.ndarray],
        ],
    ],
    output_folder: Path,
) -> None:
    """Plot median profile and interquartile range."""

    gait_percent = np.linspace(
        0,
        100,
        NUMBER_OF_GAIT_POINTS,
    )

    conditions = list(
        EMG_FILES.keys()
    )

    muscle_order = [
        "RF",
        "VM",
        "VL",
        "BF",
        "TA",
        "GM",
    ]

    figure, axes = plt.subplots(
        3,
        2,
        figsize=(16, 9),
        sharex=True,
    )

    axes = axes.flatten()

    for axis, muscle in zip(
        axes,
        muscle_order,
    ):

        for condition in conditions:

            median_profile = (
                profiles[condition][muscle][
                    "Median"
                ]
            )

            q25_profile = (
                profiles[condition][muscle]["Q25"]
            )

            q75_profile = (
                profiles[condition][muscle]["Q75"]
            )

            line = axis.plot(
                gait_percent,
                median_profile,
                linewidth=2.0,
                label=condition,
            )[0]

            axis.fill_between(
                gait_percent,
                q25_profile,
                q75_profile,
                alpha=0.14,
                color=line.get_color(),
                linewidth=0,
            )

        axis.set_title(
            MUSCLE_TITLES[muscle],
            fontsize=13,
            fontweight="bold",
        )

        axis.set_xlim(
            0,
            100,
        )

        axis.set_xlabel(
            "Right gait cycle (%)",
        )

        axis.set_ylabel(
            "Processed EMG (V)",
        )

        axis.grid(
            True,
            alpha=0.3,
        )

        axis.ticklabel_format(
            axis="y",
            style="sci",
            scilimits=(-3, 3),
        )

    figure.suptitle(
        "Time-normalised right gait-cycle EMG: Tianyu\n"
        "Median and interquartile range across gait cycles",
        fontsize=17,
        fontweight="bold",
        y=0.995,
    )

    handles, labels = axes[0].get_legend_handles_labels()

    figure.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.945),
        ncol=4,
        frameon=False,
    )

    figure.tight_layout(
        rect=[
            0.02,
            0.03,
            0.99,
            0.90,
        ]
    )

    figure.savefig(
        output_folder
        / "Median_IQR_Time_Normalised_Right_Gait_EMG.png",
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(figure)


def plot_normalised_median_activation(
    normalised_summary: pd.DataFrame,
    output_folder: Path,
) -> None:
    """Plot median activation normalised to no exosuit."""

    condition_order = [
        "No exosuit",
        "Exosuit off",
        "Exosuit on - constant",
        "Exosuit on - variable",
    ]

    muscle_order = [
        "RF",
        "VM",
        "VL",
        "BF",
        "TA",
        "GM",
    ]

    pivot_table = (
        normalised_summary
        .pivot(
            index="Muscle",
            columns="Condition",
            values=(
                "Normalised median activation (%)"
            ),
        )
        .reindex(
            index=muscle_order,
            columns=condition_order,
        )
    )

    figure, axis = plt.subplots(
        figsize=(13, 7),
    )

    x_positions = np.arange(
        len(muscle_order)
    )

    number_of_conditions = len(
        condition_order
    )

    total_width = 0.82

    bar_width = (
        total_width / number_of_conditions
    )

    for condition_index, condition in enumerate(
        condition_order
    ):

        offset = (
            condition_index
            - (number_of_conditions - 1) / 2
        ) * bar_width

        values = pivot_table[
            condition
        ].to_numpy(dtype=float)

        axis.bar(
            x_positions + offset,
            values,
            width=bar_width,
            label=condition,
        )

    axis.axhline(
        100,
        linestyle="--",
        linewidth=1.5,
        label="No-exosuit reference",
    )

    axis.set_xticks(
        x_positions
    )

    axis.set_xticklabels(
        [
            MUSCLE_TITLES[muscle]
            for muscle in muscle_order
        ],
        rotation=20,
        ha="right",
    )

    axis.set_ylabel(
        "Normalised median activation (%)"
    )

    axis.set_title(
        "Median EMG activation normalised to no-exosuit walking\n"
        f"Analysis window: "
        f"{MEDIAN_WINDOW_START_PERCENT}–"
        f"{MEDIAN_WINDOW_END_PERCENT}% of right gait cycle",
        fontweight="bold",
    )

    axis.grid(
        True,
        axis="y",
        alpha=0.3,
    )

    axis.legend(
        frameon=False,
    )

    figure.tight_layout()

    figure.savefig(
        output_folder
        / "Normalised_Median_Activation.png",
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(figure)


def plot_heel_strike_diagnostic(
    condition: str,
    gait_file: Path,
    heel_strikes: np.ndarray,
    heel_source: str,
    output_folder: Path,
) -> None:
    """Plot the heel-strike signal and detected events."""

    dataframe = read_gait_csv(
        gait_file
    )

    dataframe["Time"] = convert_to_numeric(
        dataframe["Time"]
    )

    dataframe = dataframe.dropna(
        subset=["Time"],
    )

    dataframe = dataframe.sort_values(
        "Time"
    )

    time = dataframe[
        "Time"
    ].to_numpy(dtype=float)

    time = time - time[0]

    if heel_source not in dataframe.columns:
        return

    signal = convert_to_numeric(
        dataframe[heel_source]
    ).to_numpy(dtype=float)

    length = min(
        len(time),
        len(signal),
    )

    time = time[:length]
    signal = signal[:length]

    figure, axis = plt.subplots(
        figsize=(14, 4),
    )

    axis.plot(
        time,
        signal,
        linewidth=1,
        label=heel_source,
    )

    for index, strike_time in enumerate(
        heel_strikes
    ):

        axis.axvline(
            strike_time,
            linewidth=0.8,
            alpha=0.5,
            label=(
                "Detected right heel strike"
                if index == 0
                else None
            ),
        )

    axis.set_title(
        f"{condition}: right heel-strike detection",
        fontweight="bold",
    )

    axis.set_xlabel(
        "Time (s)"
    )

    axis.set_ylabel(
        heel_source
    )

    axis.grid(
        True,
        alpha=0.3,
    )

    axis.legend(
        frameon=False,
    )

    figure.tight_layout()

    safe_condition_name = (
        condition
        .replace(" ", "_")
        .replace("-", "")
    )

    figure.savefig(
        output_folder
        / (
            f"Heel_Strike_Diagnostic_"
            f"{safe_condition_name}.png"
        ),
        dpi=250,
        bbox_inches="tight",
    )

    plt.close(figure)


# =====================================================================
# SAVING RESULTS
# =====================================================================

def save_results(
    all_results: Dict[str, Dict[str, object]],
    profile_dataframe: pd.DataFrame,
    all_cycle_metrics: pd.DataFrame,
    median_summary: pd.DataFrame,
    normalised_summary: pd.DataFrame,
    output_folder: Path,
) -> None:
    """Save all analysis tables."""

    output_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    profile_dataframe.to_csv(
        output_folder
        / "Time_Normalised_EMG_Profiles.csv",
        index=False,
    )

    all_cycle_metrics.to_csv(
        output_folder
        / "Individual_Gait_Cycle_EMG_Metrics.csv",
        index=False,
    )

    median_summary.to_csv(
        output_folder
        / "Median_Activation_Summary.csv",
        index=False,
    )

    normalised_summary.to_csv(
        output_folder
        / "Normalised_Median_Activation_Summary.csv",
        index=False,
    )

    condition_information_rows = []

    for condition, result in all_results.items():

        heel_strikes = result["Heel strikes"]

        gait_durations = np.diff(
            heel_strikes
        )

        valid_durations = gait_durations[
            (
                gait_durations
                >= MINIMUM_GAIT_CYCLE_SECONDS
            )
            & (
                gait_durations
                <= MAXIMUM_GAIT_CYCLE_SECONDS
            )
        ]

        condition_information_rows.append(
            {
                "Condition": condition,
                "EMG file": (
                    EMG_FILES[condition].name
                ),
                "Gait file": (
                    GAIT_FILES[condition].name
                ),
                "EMG sampling frequency (Hz)": (
                    result["Sampling frequency"]
                ),
                "EMG time offset (s)": (
                    EMG_TIME_OFFSETS_SECONDS[
                        condition
                    ]
                ),
                "Heel-strike source": (
                    result["Heel source"]
                ),
                "Detected heel strikes": (
                    len(heel_strikes)
                ),
                "Accepted gait cycles": (
                    result["Number of cycles"]
                ),
                "Median gait-cycle duration (s)": (
                    np.median(valid_durations)
                    if len(valid_durations) > 0
                    else np.nan
                ),
            }
        )

    condition_information = pd.DataFrame(
        condition_information_rows
    )

    excel_path = (
        output_folder
        / "Tianyu_Right_Gait_Cycle_EMG_Analysis.xlsx"
    )

    with pd.ExcelWriter(
        excel_path,
        engine="openpyxl",
    ) as writer:

        condition_information.to_excel(
            writer,
            sheet_name="Condition information",
            index=False,
        )

        median_summary.to_excel(
            writer,
            sheet_name="Median activation",
            index=False,
        )

        normalised_summary.to_excel(
            writer,
            sheet_name="Normalised median",
            index=False,
        )

        all_cycle_metrics.to_excel(
            writer,
            sheet_name="Individual cycles",
            index=False,
        )

        profile_dataframe.to_excel(
            writer,
            sheet_name="Gait cycle profiles",
            index=False,
        )


# =====================================================================
# MAIN PROGRAM
# =====================================================================

def main() -> None:
    """Run the complete analysis."""

    print("\n" + "=" * 78)
    print("TIME-NORMALISED RIGHT GAIT-CYCLE EMG ANALYSIS")
    print("=" * 78)

    OUTPUT_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    all_results: Dict[
        str,
        Dict[str, object]
    ] = {}

    all_cycle_metric_frames = []

    for condition in EMG_FILES:

        result = process_condition(
            condition=condition,
            emg_file=EMG_FILES[condition],
            gait_file=GAIT_FILES[condition],
        )

        all_results[condition] = result

        all_cycle_metric_frames.append(
            result["Cycle metrics"]
        )

        plot_heel_strike_diagnostic(
            condition=condition,
            gait_file=GAIT_FILES[condition],
            heel_strikes=result["Heel strikes"],
            heel_source=result["Heel source"],
            output_folder=OUTPUT_FOLDER,
        )

    all_cycle_metrics = pd.concat(
        all_cycle_metric_frames,
        ignore_index=True,
    )

    profiles, profile_dataframe = (
        calculate_condition_profiles(
            all_results
        )
    )

    median_summary, normalised_summary = (
        create_median_summary(
            all_cycle_metrics
        )
    )

    plot_mean_sd_profiles(
        profiles=profiles,
        all_results=all_results,
        output_folder=OUTPUT_FOLDER,
    )

    plot_median_iqr_profiles(
        profiles=profiles,
        output_folder=OUTPUT_FOLDER,
    )

    plot_normalised_median_activation(
        normalised_summary=normalised_summary,
        output_folder=OUTPUT_FOLDER,
    )

    save_results(
        all_results=all_results,
        profile_dataframe=profile_dataframe,
        all_cycle_metrics=all_cycle_metrics,
        median_summary=median_summary,
        normalised_summary=normalised_summary,
        output_folder=OUTPUT_FOLDER,
    )

    print("\n" + "=" * 78)
    print("ANALYSIS COMPLETED")
    print("=" * 78)

    print(
        f"\nResults saved in:\n{OUTPUT_FOLDER}"
    )

    print(
        "\nMain figure:"
        "\nMean_SD_Time_Normalised_Right_Gait_EMG.png"
    )

    print(
        "\nMedian profile figure:"
        "\nMedian_IQR_Time_Normalised_Right_Gait_EMG.png"
    )

    print(
        "\nNormalised median figure:"
        "\nNormalised_Median_Activation.png"
    )

    print(
        "\nExcel results:"
        "\nTianyu_Right_Gait_Cycle_EMG_Analysis.xlsx"
    )


if __name__ == "__main__":
    main()