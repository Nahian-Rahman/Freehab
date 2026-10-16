"""
=============================================================
FOUR-CONDITION EMG PROCESSING AND COMPARISON
=============================================================

Conditions:
1. Walking without suit
2. Walking with suit but no actuation
3. Walking with constant-pressure actuation
4. Walking with variable-pressure actuation

The variable-pressure trial is also divided into:
- Before pressure increase
- After pressure increase

EMG channels:
- RF: Rectus Femoris
- VM: Vastus Medialis
- VL: Vastus Lateralis
- BF: Biceps Femoris
- TA: Tibialis Anterior
- GM: Gastrocnemius Medialis

Processing:
- Reads CSV files
- Uses the first "X [s]" column as time
- Ignores accelerometer columns
- Removes missing values
- Removes DC offset
- Applies 50 Hz notch filtering
- Applies 20–450 Hz band-pass filtering
- Full-wave rectification
- Creates a 6 Hz linear envelope
- Calculates moving RMS
- Calculates whole-trial RMS
- Calculates integrated EMG
- Normalizes activity to walking without suit
- Compares pressure before and after increase
- Saves processed signals, tables and plots

Required packages:

pip install numpy pandas scipy matplotlib openpyxl
=============================================================
"""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.signal import butter, sosfiltfilt, iirnotch, filtfilt


# =============================================================
# USER SETTINGS
# =============================================================

# Change these filenames to match your four CSV files.
FILES = {
    "Without suit": "Tianyu_nosuitWalking.xlsx",
    "Suit, no actuation": "Tianyu_withsuitWalking_noActuation.xlsx",
    "Constant pressure": "Tianyu_suitWalkingConstantActuation.xlsx",
    "Variable pressure": "Tianyu_suitWalkingVariableActuation.xlsx",
}


# Folder where all results will be saved.
OUTPUT_FOLDER = Path("EMG_four_condition_analysis")


# =============================================================
# EXACT EMG COLUMN NAMES
# =============================================================

EMG_COLUMNS = {
    "RF": "RF: EMG 1 [Volts]",
    "VM": "VM: EMG 2 [Volts]",
    "VL": "VL: EMG 3 [Volts]",
    "BF": "BF: EMG 4 [Volts]",
    "TA": "TA: EMG 5 [Volts]",
    "GM": "GM: EMG 6 [Volts]",
}


# =============================================================
# SAMPLING FREQUENCY
# =============================================================

# Leave this as None to calculate sampling frequency from X [s].
#
# Set a number such as 1000.0 if you know the exact sampling rate
# and prefer to use that value.
SAMPLING_FREQUENCY = None


# =============================================================
# FILTER SETTINGS
# =============================================================

NOTCH_FREQUENCY_HZ = 50.0
NOTCH_QUALITY_FACTOR = 30.0

BANDPASS_LOW_HZ = 20.0
BANDPASS_HIGH_HZ = 450.0

ENVELOPE_LOWPASS_HZ = 6.0

# RMS calculation window: 100 ms.
RMS_WINDOW_SECONDS = 0.100


# =============================================================
# RECORDING TRIMMING
# =============================================================

# Remove start and stop artefacts.
TRIM_START_SECONDS = 5.0
TRIM_END_SECONDS = 5.0


# =============================================================
# VARIABLE-PRESSURE SETTINGS
# =============================================================

# Time when pressure was increased in the original recording.
VARIABLE_PRESSURE_CHANGE_SECONDS = 30.0

# Remove a small transition period around the pressure change.
#
# For example:
# pressure increase at 30 seconds
# exclusion = 1 second
#
# Before section ends at 29 seconds.
# After section starts at 31 seconds.
PRESSURE_CHANGE_EXCLUSION_SECONDS = 1.0


# =============================================================
# PLOT SETTINGS
# =============================================================

SHOW_PLOTS = True
FIGURE_DPI = 300


# =============================================================
# COLUMN AND FILE FUNCTIONS
# =============================================================

def clean_column_name(column_name):
    """
    Remove hidden characters and unnecessary spaces from a column name.
    """

    return (
        str(column_name)
        .replace("\ufeff", "")
        .replace("\r", "")
        .replace("\n", " ")
        .strip()
    )


def normalize_column_name(column_name):
    """
    Normalize a column name for flexible matching.

    Capitalization, spaces and punctuation are ignored.
    """

    return "".join(
        character.lower()
        for character in str(column_name)
        if character.isalnum()
    )


def read_emg_file(filename):
    """
    Read one Excel or CSV file and clean the column names.

    Supported formats:
    - .xlsx
    - .xls
    - .csv
    """

    file_path = Path(filename)

    if not file_path.exists():
        raise FileNotFoundError(
            f"\nFile not found:\n"
            f"{file_path.resolve()}\n\n"
            f"Please correct the filename in the FILES dictionary."
        )

    extension = file_path.suffix.lower()

    if extension in [".xlsx", ".xls"]:

        # Reads the first worksheet by default.
        dataframe = pd.read_excel(
            file_path,
            sheet_name=0,
        )

    elif extension == ".csv":

        try:
            dataframe = pd.read_csv(file_path)

            if len(dataframe.columns) == 1:
                dataframe = pd.read_csv(
                    file_path,
                    sep=None,
                    engine="python",
                )

        except Exception:
            dataframe = pd.read_csv(
                file_path,
                sep=None,
                engine="python",
            )

    else:
        raise ValueError(
            f"\nUnsupported file format: {extension}\n"
            f"Please use .xlsx, .xls or .csv."
        )

    dataframe.columns = [
        clean_column_name(column)
        for column in dataframe.columns
    ]

    return dataframe



def find_matching_column(dataframe, required_column):
    """
    Find a column using exact matching first and normalized matching second.
    """

    if required_column in dataframe.columns:
        return required_column

    required_normalized = normalize_column_name(required_column)

    for existing_column in dataframe.columns:

        existing_normalized = normalize_column_name(existing_column)

        if existing_normalized == required_normalized:
            return existing_column

    return None


def identify_emg_columns(dataframe):
    """
    Identify the six EMG columns.

    Accelerometer columns are ignored.
    """

    detected_columns = {}

    for muscle, required_column in EMG_COLUMNS.items():

        detected_column = find_matching_column(
            dataframe=dataframe,
            required_column=required_column,
        )

        if detected_column is None:
            raise ValueError(
                f"\nCould not find the EMG column for {muscle}.\n\n"
                f"Expected column:\n"
                f"{required_column}\n\n"
                f"Available columns:\n"
                f"{list(dataframe.columns)}"
            )

        detected_columns[muscle] = detected_column

    return detected_columns


def identify_time_column(dataframe):
    """
    Identify the first X [s] time column.

    Because your CSV contains several columns named X [s], pandas usually
    renames them as:

    X [s]
    X [s].1
    X [s].2
    X [s].3
    ...

    This function uses the first X [s] column.
    """

    preferred_names = [
        "X [s]",
        "Time [s]",
        "Time (s)",
        "Time",
        "time",
    ]

    for preferred_name in preferred_names:

        if preferred_name in dataframe.columns:
            return preferred_name

    for column in dataframe.columns:

        cleaned_column = str(column).strip().lower()

        if cleaned_column.startswith("x [s]"):
            return column

    raise ValueError(
        "\nCould not find the time column.\n"
        "The code expected a column named X [s]."
    )


def convert_to_numeric_array(series):
    """
    Convert a pandas column to a floating-point NumPy array.
    """

    return pd.to_numeric(
        series,
        errors="coerce",
    ).to_numpy(dtype=float)


# =============================================================
# TIME AND SIGNAL PREPARATION
# =============================================================

def prepare_time_and_emg(
    dataframe,
    time_column,
    detected_emg_columns,
):
    """
    Extract the time and six EMG channels.

    Missing EMG samples are interpolated.
    """

    time = convert_to_numeric_array(
        dataframe[time_column]
    )

    emg_signals = np.column_stack([
        convert_to_numeric_array(
            dataframe[detected_emg_columns[muscle]]
        )
        for muscle in EMG_COLUMNS
    ])

    # Keep rows with a valid time and at least one valid EMG value.
    valid_time = np.isfinite(time)

    at_least_one_valid_emg = np.any(
        np.isfinite(emg_signals),
        axis=1,
    )

    valid_rows = valid_time & at_least_one_valid_emg

    time = time[valid_rows]
    emg_signals = emg_signals[valid_rows, :]

    if len(time) < 2:
        raise ValueError(
            "Not enough valid samples remained after cleaning."
        )

    # Interpolate missing samples separately for each muscle.
    for channel_index in range(emg_signals.shape[1]):

        channel = pd.Series(
            emg_signals[:, channel_index]
        )

        channel = channel.interpolate(
            method="linear",
            limit_direction="both",
        )

        emg_signals[:, channel_index] = channel.to_numpy(
            dtype=float
        )

    # Make time start at zero.
    time = time - time[0]

    return time, emg_signals


def calculate_sampling_frequency(time):
    """
    Calculate the sampling frequency from the time vector.
    """

    time_differences = np.diff(time)

    valid_differences = time_differences[
        np.isfinite(time_differences)
        & (time_differences > 0)
    ]

    if len(valid_differences) == 0:
        raise ValueError(
            "Could not calculate sampling frequency from X [s]."
        )

    median_time_step = np.median(valid_differences)

    calculated_frequency = 1.0 / median_time_step

    if SAMPLING_FREQUENCY is None:

        sampling_frequency = calculated_frequency

    else:

        sampling_frequency = float(SAMPLING_FREQUENCY)

        percentage_difference = (
            abs(
                sampling_frequency
                - calculated_frequency
            )
            / calculated_frequency
            * 100.0
        )

        if percentage_difference > 5.0:
            warnings.warn(
                f"The specified sampling frequency is "
                f"{sampling_frequency:.2f} Hz, but X [s] indicates "
                f"approximately {calculated_frequency:.2f} Hz."
            )

    return sampling_frequency, calculated_frequency


def trim_recording(time, emg_signals):
    """
    Remove the beginning and end of the recording.
    """

    start_time = max(
        0.0,
        float(TRIM_START_SECONDS),
    )

    end_time = (
        time[-1]
        - max(0.0, float(TRIM_END_SECONDS))
    )

    if end_time <= start_time:

        warnings.warn(
            "The requested trimming would remove the entire recording. "
            "Trimming has therefore been skipped."
        )

        return time, emg_signals

    selected_rows = (
        (time >= start_time)
        & (time <= end_time)
    )

    trimmed_time = time[selected_rows]
    trimmed_emg = emg_signals[selected_rows, :]

    if len(trimmed_time) < 2:
        raise ValueError(
            "Not enough samples remained after trimming."
        )

    trimmed_time = trimmed_time - trimmed_time[0]

    return trimmed_time, trimmed_emg


# =============================================================
# EMG FILTERING FUNCTIONS
# =============================================================

def determine_upper_bandpass_frequency(sampling_frequency):
    """
    Ensure that the upper band-pass cutoff is below Nyquist frequency.
    """

    nyquist_frequency = sampling_frequency / 2.0

    if BANDPASS_HIGH_HZ < nyquist_frequency:
        return BANDPASS_HIGH_HZ

    adjusted_upper_frequency = nyquist_frequency * 0.90

    warnings.warn(
        f"The requested upper band-pass cutoff of "
        f"{BANDPASS_HIGH_HZ:.1f} Hz is too high for a sampling "
        f"frequency of {sampling_frequency:.1f} Hz.\n"
        f"The upper cutoff has been changed to "
        f"{adjusted_upper_frequency:.1f} Hz."
    )

    if adjusted_upper_frequency <= BANDPASS_LOW_HZ:
        raise ValueError(
            "The sampling frequency is too low for the requested "
            "EMG band-pass filter."
        )

    return adjusted_upper_frequency


def apply_notch_filter(signal, sampling_frequency):
    """
    Apply a zero-phase 50 Hz notch filter.
    """

    nyquist_frequency = sampling_frequency / 2.0

    if NOTCH_FREQUENCY_HZ >= nyquist_frequency:

        warnings.warn(
            "The 50 Hz notch filter was skipped because the "
            "Nyquist frequency is below 50 Hz."
        )

        return signal.copy()

    numerator, denominator = iirnotch(
        w0=NOTCH_FREQUENCY_HZ,
        Q=NOTCH_QUALITY_FACTOR,
        fs=sampling_frequency,
    )

    notch_filtered_signal = filtfilt(
        numerator,
        denominator,
        signal,
    )

    return notch_filtered_signal


def apply_bandpass_filter(signal, sampling_frequency):
    """
    Apply a fourth-order zero-phase Butterworth band-pass filter.
    """

    upper_frequency = determine_upper_bandpass_frequency(
        sampling_frequency
    )

    second_order_sections = butter(
        N=4,
        Wn=[
            BANDPASS_LOW_HZ,
            upper_frequency,
        ],
        btype="bandpass",
        fs=sampling_frequency,
        output="sos",
    )

    filtered_signal = sosfiltfilt(
        second_order_sections,
        signal,
    )

    return filtered_signal


def calculate_linear_envelope(
    rectified_signal,
    sampling_frequency,
):
    """
    Low-pass filter the rectified EMG to create a linear envelope.
    """

    nyquist_frequency = sampling_frequency / 2.0

    if ENVELOPE_LOWPASS_HZ >= nyquist_frequency:
        raise ValueError(
            "The EMG envelope cutoff is above the Nyquist frequency."
        )

    second_order_sections = butter(
        N=4,
        Wn=ENVELOPE_LOWPASS_HZ,
        btype="lowpass",
        fs=sampling_frequency,
        output="sos",
    )

    envelope = sosfiltfilt(
        second_order_sections,
        rectified_signal,
    )

    # Remove tiny negative values produced by filtering.
    envelope = np.maximum(
        envelope,
        0.0,
    )

    return envelope


def calculate_moving_rms(
    filtered_signal,
    sampling_frequency,
):
    """
    Calculate moving RMS using a centered window.
    """

    window_samples = max(
        1,
        int(
            round(
                RMS_WINDOW_SECONDS
                * sampling_frequency
            )
        ),
    )

    squared_signal = np.square(
        filtered_signal
    )

    moving_mean_square = (
        pd.Series(squared_signal)
        .rolling(
            window=window_samples,
            center=True,
            min_periods=1,
        )
        .mean()
        .to_numpy(dtype=float)
    )

    moving_rms = np.sqrt(
        moving_mean_square
    )

    return moving_rms


def process_single_emg_channel(
    raw_signal,
    sampling_frequency,
):
    """
    Process one complete EMG channel.
    """

    raw_signal = np.asarray(
        raw_signal,
        dtype=float,
    )

    # Remove DC offset.
    dc_removed_signal = (
        raw_signal
        - np.mean(raw_signal)
    )

    # Remove 50 Hz mains interference.
    notch_filtered_signal = apply_notch_filter(
        signal=dc_removed_signal,
        sampling_frequency=sampling_frequency,
    )

    # Retain the main EMG frequency content.
    bandpass_filtered_signal = apply_bandpass_filter(
        signal=notch_filtered_signal,
        sampling_frequency=sampling_frequency,
    )

    # Full-wave rectification.
    rectified_signal = np.abs(
        bandpass_filtered_signal
    )

    # Smooth linear envelope.
    envelope = calculate_linear_envelope(
        rectified_signal=rectified_signal,
        sampling_frequency=sampling_frequency,
    )

    # Moving RMS.
    moving_rms = calculate_moving_rms(
        filtered_signal=bandpass_filtered_signal,
        sampling_frequency=sampling_frequency,
    )

    return {
        "raw": raw_signal,
        "dc_removed": dc_removed_signal,
        "notch_filtered": notch_filtered_signal,
        "filtered": bandpass_filtered_signal,
        "rectified": rectified_signal,
        "envelope": envelope,
        "moving_rms": moving_rms,
    }


# =============================================================
# COMPLETE FILE PROCESSING
# =============================================================

def process_complete_file(condition, filename):
    """
    Read and process all six EMG channels from one CSV file.
    """

    print("\n" + "=" * 75)
    print(f"Condition: {condition}")
    print(f"File: {filename}")
    print("=" * 75)

    #dataframe = read_emg_csv(filename)
    dataframe = read_emg_file(filename)

    print("\nColumns found in the CSV file:")

    for column_index, column in enumerate(dataframe.columns):
        print(f"{column_index:3d}: {column}")

    time_column = identify_time_column(dataframe)

    detected_emg_columns = identify_emg_columns(dataframe)

    print(f"\nTime column used: {time_column}")

    print("\nEMG columns used:")

    for muscle, column in detected_emg_columns.items():
        print(f"  {muscle}: {column}")

    time, raw_emg = prepare_time_and_emg(
        dataframe=dataframe,
        time_column=time_column,
        detected_emg_columns=detected_emg_columns,
    )

    sampling_frequency, calculated_frequency = (
        calculate_sampling_frequency(time)
    )

    original_duration = time[-1] - time[0]

    time, raw_emg = trim_recording(
        time=time,
        emg_signals=raw_emg,
    )

    analysed_duration = time[-1] - time[0]

    print(
        f"\nSampling frequency calculated from X [s]: "
        f"{calculated_frequency:.3f} Hz"
    )

    print(
        f"Sampling frequency used for processing: "
        f"{sampling_frequency:.3f} Hz"
    )

    print(
        f"Original recording duration: "
        f"{original_duration:.3f} seconds"
    )

    print(
        f"Analysed recording duration: "
        f"{analysed_duration:.3f} seconds"
    )

    print(
        f"Number of analysed samples: "
        f"{len(time)}"
    )

    processed_muscles = {}

    muscle_names = list(EMG_COLUMNS.keys())

    for muscle_index, muscle in enumerate(muscle_names):

        print(f"Processing {muscle}...")

        processed_muscles[muscle] = process_single_emg_channel(
            raw_signal=raw_emg[:, muscle_index],
            sampling_frequency=sampling_frequency,
        )

    return {
        "condition": condition,
        "filename": filename,
        "time": time,
        "sampling_frequency": sampling_frequency,
        "processed": processed_muscles,
        "original_duration": original_duration,
        "analysed_duration": analysed_duration,
    }


# =============================================================
# EMG ACTIVITY METRICS
# =============================================================

def calculate_segment_metrics(
    trial,
    segment_name,
    start_time=None,
    end_time=None,
):
    """
    Calculate EMG activity measures for one trial or trial segment.
    """

    time = trial["time"]

    selected_rows = np.ones(
        len(time),
        dtype=bool,
    )

    if start_time is not None:
        selected_rows &= time >= start_time

    if end_time is not None:
        selected_rows &= time < end_time

    selected_time = time[selected_rows]

    if len(selected_time) < 2:

        warnings.warn(
            f"Not enough samples were available for {segment_name}."
        )

        return []

    segment_time = selected_time - selected_time[0]

    segment_duration = (
        segment_time[-1]
        - segment_time[0]
    )

    result_rows = []

    for muscle in EMG_COLUMNS:

        muscle_data = trial["processed"][muscle]

        filtered_signal = muscle_data[
            "filtered"
        ][selected_rows]

        rectified_signal = muscle_data[
            "rectified"
        ][selected_rows]

        envelope = muscle_data[
            "envelope"
        ][selected_rows]

        moving_rms = muscle_data[
            "moving_rms"
        ][selected_rows]

        overall_rms = np.sqrt(
            np.mean(
                np.square(filtered_signal)
            )
        )

        mean_moving_rms = np.mean(
            moving_rms
        )

        median_moving_rms = np.median(
            moving_rms
        )

        mean_envelope = np.mean(
            envelope
        )

        median_envelope = np.median(
            envelope
        )

        peak_envelope_95 = np.percentile(
            envelope,
            95,
        )

        peak_rms_95 = np.percentile(
            moving_rms,
            95,
        )

        mean_rectified_emg = np.mean(
            rectified_signal
        )

        integrated_emg = np.trapezoid(
            rectified_signal,
            x=segment_time,
        )

        if segment_duration > 0:

            integrated_emg_per_second = (
                integrated_emg
                / segment_duration
            )

        else:

            integrated_emg_per_second = np.nan

        result_rows.append({
            "Condition": segment_name,
            "Muscle": muscle,
            "Start time in processed trial (s)": selected_time[0],
            "End time in processed trial (s)": selected_time[-1],
            "Duration (s)": segment_duration,
            "Overall RMS (V)": overall_rms,
            "Mean moving RMS (V)": mean_moving_rms,
            "Median moving RMS (V)": median_moving_rms,
            "95th percentile moving RMS (V)": peak_rms_95,
            "Mean envelope (V)": mean_envelope,
            "Median envelope (V)": median_envelope,
            "95th percentile envelope (V)": peak_envelope_95,
            "Mean rectified EMG (V)": mean_rectified_emg,
            "Integrated EMG (V.s)": integrated_emg,
            "Integrated EMG per second (V)": (
                integrated_emg_per_second
            ),
        })

    return result_rows


def calculate_all_metrics(processed_trials):
    """
    Calculate metrics for all conditions.

    The variable-pressure trial is also separated before and after
    the pressure increase.
    """

    all_result_rows = []

    # Whole-trial results.
    for condition, trial in processed_trials.items():

        trial_rows = calculate_segment_metrics(
            trial=trial,
            segment_name=condition,
        )

        all_result_rows.extend(trial_rows)

    # Variable-pressure before/after analysis.
    variable_condition = "Variable pressure"

    if variable_condition in processed_trials:

        variable_trial = processed_trials[
            variable_condition
        ]

        # The processed trial starts after removing TRIM_START_SECONDS.
        pressure_change_time_in_processed_trial = (
            VARIABLE_PRESSURE_CHANGE_SECONDS
            - TRIM_START_SECONDS
        )

        before_end_time = (
            pressure_change_time_in_processed_trial
            - PRESSURE_CHANGE_EXCLUSION_SECONDS
        )

        after_start_time = (
            pressure_change_time_in_processed_trial
            + PRESSURE_CHANGE_EXCLUSION_SECONDS
        )

        if before_end_time > 0:

            before_rows = calculate_segment_metrics(
                trial=variable_trial,
                segment_name=(
                    "Variable pressure - before increase"
                ),
                start_time=0.0,
                end_time=before_end_time,
            )

            all_result_rows.extend(before_rows)

        else:

            warnings.warn(
                "The pressure-change time occurs before the available "
                "processed data. The before-pressure segment was skipped."
            )

        if after_start_time < variable_trial["time"][-1]:

            after_rows = calculate_segment_metrics(
                trial=variable_trial,
                segment_name=(
                    "Variable pressure - after increase"
                ),
                start_time=after_start_time,
                end_time=None,
            )

            all_result_rows.extend(after_rows)

        else:

            warnings.warn(
                "The pressure-change time occurs after the available "
                "processed data. The after-pressure segment was skipped."
            )

    return pd.DataFrame(all_result_rows)


# =============================================================
# NORMALIZATION
# =============================================================

def normalize_to_without_suit(metrics_dataframe):
    """
    Normalize every muscle to its own walking-without-suit RMS.

    Without suit = 100%.

    This is not MVC normalization.
    """

    normalized_dataframe = metrics_dataframe.copy()

    reference_condition = "Without suit"

    reference_rows = normalized_dataframe[
        normalized_dataframe["Condition"]
        == reference_condition
    ].set_index("Muscle")

    if reference_rows.empty:
        raise ValueError(
            "The reference condition 'Without suit' was not found."
        )

    metrics_to_normalize = [
        "Overall RMS (V)",
        "Mean moving RMS (V)",
        "Mean envelope (V)",
        "Mean rectified EMG (V)",
        "Integrated EMG per second (V)",
    ]

    for metric in metrics_to_normalize:

        normalized_column_name = (
            metric
            + " (% of without suit)"
        )

        normalized_values = []

        for _, row in normalized_dataframe.iterrows():

            muscle = row["Muscle"]

            reference_value = reference_rows.loc[
                muscle,
                metric,
            ]

            if isinstance(reference_value, pd.Series):
                reference_value = reference_value.iloc[0]

            if (
                not np.isfinite(reference_value)
                or reference_value == 0
            ):

                normalized_value = np.nan

            else:

                normalized_value = (
                    row[metric]
                    / reference_value
                    * 100.0
                )

            normalized_values.append(
                normalized_value
            )

        normalized_dataframe[
            normalized_column_name
        ] = normalized_values

    return normalized_dataframe


# =============================================================
# SAVE PROCESSED SIGNALS
# =============================================================

def create_safe_filename(text):
    """
    Convert a condition name into a filename-safe string.
    """

    return (
        text.lower()
        .replace(" ", "_")
        .replace(",", "")
        .replace("-", "_")
        .replace("/", "_")
    )


def save_processed_signals(processed_trials):
    """
    Save raw and processed EMG signals for each condition.
    """

    processed_folder = (
        OUTPUT_FOLDER
        / "processed_signals"
    )

    processed_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    for condition, trial in processed_trials.items():

        output_data = {
            "Time (s)": trial["time"]
        }

        for muscle in EMG_COLUMNS:

            muscle_data = trial[
                "processed"
            ][muscle]

            output_data[
                f"{muscle} raw (V)"
            ] = muscle_data["raw"]

            output_data[
                f"{muscle} DC removed (V)"
            ] = muscle_data["dc_removed"]

            output_data[
                f"{muscle} notch filtered (V)"
            ] = muscle_data["notch_filtered"]

            output_data[
                f"{muscle} bandpass filtered (V)"
            ] = muscle_data["filtered"]

            output_data[
                f"{muscle} rectified (V)"
            ] = muscle_data["rectified"]

            output_data[
                f"{muscle} envelope (V)"
            ] = muscle_data["envelope"]

            output_data[
                f"{muscle} moving RMS (V)"
            ] = muscle_data["moving_rms"]

        output_dataframe = pd.DataFrame(
            output_data
        )

        output_filename = (
            processed_folder
            / (
                create_safe_filename(condition)
                + "_processed.csv"
            )
        )

        output_dataframe.to_csv(
            output_filename,
            index=False,
        )


# =============================================================
# PLOT RAW AND FILTERED EXAMPLES
# =============================================================

def plot_raw_and_filtered_signals(processed_trials):
    """
    Plot raw, filtered and envelope signals for every condition.
    """

    muscles = list(EMG_COLUMNS.keys())

    for condition, trial in processed_trials.items():

        time = trial["time"]

        for muscle in muscles:

            muscle_data = trial["processed"][muscle]

            figure, axis = plt.subplots(
                figsize=(13, 6)
            )

            axis.plot(
                time,
                muscle_data["raw"],
                linewidth=0.5,
                alpha=0.6,
                label="Raw EMG",
            )

            axis.plot(
                time,
                muscle_data["filtered"],
                linewidth=0.5,
                label="Band-pass filtered EMG",
            )

            axis.plot(
                time,
                muscle_data["envelope"],
                linewidth=1.2,
                label="Linear envelope",
            )

            axis.set_xlabel("Time (s)")
            axis.set_ylabel("EMG (V)")

            axis.set_title(
                f"{muscle}: {condition}"
            )

            axis.grid(
                True,
                alpha=0.3,
            )

            axis.legend()

            figure.tight_layout()

            filename = (
                "signal_"
                + create_safe_filename(condition)
                + "_"
                + muscle.lower()
                + ".png"
            )

            figure.savefig(
                OUTPUT_FOLDER / filename,
                dpi=FIGURE_DPI,
                bbox_inches="tight",
            )

            if SHOW_PLOTS:
                plt.show()
            else:
                plt.close(figure)


# =============================================================
# PLOT EMG ENVELOPES
# =============================================================

def plot_envelopes_for_each_condition(processed_trials):
    """
    Plot all six EMG envelopes for every condition.
    """

    muscles = list(EMG_COLUMNS.keys())

    for condition, trial in processed_trials.items():

        figure, axes = plt.subplots(
            nrows=6,
            ncols=1,
            figsize=(13, 14),
            sharex=True,
        )

        time = trial["time"]

        for axis, muscle in zip(
            axes,
            muscles,
        ):

            envelope = trial[
                "processed"
            ][muscle]["envelope"]

            axis.plot(
                time,
                envelope,
                linewidth=0.8,
            )

            axis.set_ylabel(
                f"{muscle}\n(V)"
            )

            axis.grid(
                True,
                alpha=0.3,
            )

        axes[-1].set_xlabel(
            "Time (s)"
        )

        figure.suptitle(
            f"EMG linear envelopes: {condition}",
            fontsize=15,
        )

        figure.tight_layout(
            rect=[0, 0, 1, 0.97]
        )

        figure.savefig(
            OUTPUT_FOLDER
            / (
                "envelopes_"
                + create_safe_filename(condition)
                + ".png"
            ),
            dpi=FIGURE_DPI,
            bbox_inches="tight",
        )

        if SHOW_PLOTS:
            plt.show()
        else:
            plt.close(figure)


# =============================================================
# PLOT FOUR-CONDITION COMPARISON
# =============================================================

def plot_four_condition_rms(metrics_dataframe):
    """
    Create six plots comparing the four conditions.
    """

    conditions = [
        "Without suit",
        "Suit, no actuation",
        "Constant pressure",
        "Variable pressure",
    ]

    muscles = list(EMG_COLUMNS.keys())

    normalized_column = (
        "Overall RMS (V) "
        "(% of without suit)"
    )

    selected_dataframe = metrics_dataframe[
        metrics_dataframe["Condition"].isin(
            conditions
        )
    ]

    figure, axes = plt.subplots(
        nrows=3,
        ncols=2,
        figsize=(14, 13),
    )

    axes = axes.flatten()

    x_positions = np.arange(
        len(conditions)
    )

    for axis, muscle in zip(
        axes,
        muscles,
    ):

        muscle_dataframe = (
            selected_dataframe[
                selected_dataframe["Muscle"]
                == muscle
            ]
            .set_index("Condition")
            .reindex(conditions)
        )

        values = muscle_dataframe[
            normalized_column
        ].to_numpy(dtype=float)

        bars = axis.bar(
            x_positions,
            values,
        )

        axis.axhline(
            y=100.0,
            linestyle="--",
            linewidth=1.0,
            label="Without-suit reference",
        )

        axis.set_title(muscle)

        axis.set_ylabel(
            "RMS activity\n"
            "(% of without suit)"
        )

        axis.set_xticks(
            x_positions
        )

        axis.set_xticklabels(
            conditions,
            rotation=25,
            ha="right",
        )

        axis.grid(
            True,
            axis="y",
            alpha=0.3,
        )

        for bar, value in zip(
            bars,
            values,
        ):

            if np.isfinite(value):

                axis.text(
                    bar.get_x()
                    + bar.get_width() / 2,
                    bar.get_height(),
                    f"{value:.1f}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

    figure.suptitle(
        "Muscle activity under four walking conditions",
        fontsize=16,
    )

    figure.tight_layout(
        rect=[0, 0, 1, 0.96]
    )

    figure.savefig(
        OUTPUT_FOLDER
        / "four_condition_normalized_RMS.png",
        dpi=FIGURE_DPI,
        bbox_inches="tight",
    )

    if SHOW_PLOTS:
        plt.show()
    else:
        plt.close(figure)


def plot_all_muscles_grouped(metrics_dataframe):
    """
    Create one grouped bar chart containing all six muscles.
    """

    conditions = [
        "Without suit",
        "Suit, no actuation",
        "Constant pressure",
        "Variable pressure",
    ]

    muscles = list(EMG_COLUMNS.keys())

    normalized_column = (
        "Overall RMS (V) "
        "(% of without suit)"
    )

    selected_dataframe = metrics_dataframe[
        metrics_dataframe["Condition"].isin(
            conditions
        )
    ]

    pivot_table = selected_dataframe.pivot(
        index="Muscle",
        columns="Condition",
        values=normalized_column,
    )

    pivot_table = pivot_table.reindex(
        index=muscles,
        columns=conditions,
    )

    figure, axis = plt.subplots(
        figsize=(14, 7)
    )

    x_positions = np.arange(
        len(muscles)
    )

    number_of_conditions = len(
        conditions
    )

    total_group_width = 0.80

    bar_width = (
        total_group_width
        / number_of_conditions
    )

    for condition_index, condition in enumerate(
        conditions
    ):

        offset = (
            condition_index
            - (
                number_of_conditions - 1
            ) / 2
        ) * bar_width

        axis.bar(
            x_positions + offset,
            pivot_table[
                condition
            ].to_numpy(dtype=float),
            width=bar_width,
            label=condition,
        )

    axis.axhline(
        y=100.0,
        linestyle="--",
        linewidth=1.0,
    )

    axis.set_xticks(
        x_positions
    )

    axis.set_xticklabels(
        muscles
    )

    axis.set_xlabel(
        "Muscle"
    )

    axis.set_ylabel(
        "RMS activity (% of without suit)"
    )

    axis.set_title(
        "Normalized EMG activity across conditions"
    )

    axis.legend()

    axis.grid(
        True,
        axis="y",
        alpha=0.3,
    )

    figure.tight_layout()

    figure.savefig(
        OUTPUT_FOLDER
        / "grouped_normalized_RMS.png",
        dpi=FIGURE_DPI,
        bbox_inches="tight",
    )

    if SHOW_PLOTS:
        plt.show()
    else:
        plt.close(figure)


# =============================================================
# HEATMAP
# =============================================================

def plot_normalized_rms_heatmap(metrics_dataframe):
    """
    Create a heatmap of normalized muscle activity.
    """

    condition_order = [
        "Without suit",
        "Suit, no actuation",
        "Constant pressure",
        "Variable pressure",
        "Variable pressure - before increase",
        "Variable pressure - after increase",
    ]

    muscles = list(EMG_COLUMNS.keys())

    normalized_column = (
        "Overall RMS (V) "
        "(% of without suit)"
    )

    pivot_table = metrics_dataframe.pivot(
        index="Muscle",
        columns="Condition",
        values=normalized_column,
    )

    available_conditions = [
        condition
        for condition in condition_order
        if condition in pivot_table.columns
    ]

    pivot_table = pivot_table.reindex(
        index=muscles,
        columns=available_conditions,
    )

    values = pivot_table.to_numpy(
        dtype=float
    )

    figure, axis = plt.subplots(
        figsize=(13, 6)
    )

    image = axis.imshow(
        values,
        aspect="auto",
    )

    axis.set_xticks(
        np.arange(
            len(available_conditions)
        )
    )

    axis.set_xticklabels(
        available_conditions,
        rotation=30,
        ha="right",
    )

    axis.set_yticks(
        np.arange(
            len(muscles)
        )
    )

    axis.set_yticklabels(
        muscles
    )

    axis.set_title(
        "EMG RMS activity\n"
        "Percentage of walking without suit"
    )

    colorbar = figure.colorbar(
        image,
        ax=axis,
    )

    colorbar.set_label(
        "RMS activity (% of without suit)"
    )

    for row_index in range(values.shape[0]):

        for column_index in range(values.shape[1]):

            value = values[
                row_index,
                column_index,
            ]

            if np.isfinite(value):

                axis.text(
                    column_index,
                    row_index,
                    f"{value:.1f}",
                    ha="center",
                    va="center",
                    fontsize=9,
                )

    figure.tight_layout()

    figure.savefig(
        OUTPUT_FOLDER
        / "normalized_RMS_heatmap.png",
        dpi=FIGURE_DPI,
        bbox_inches="tight",
    )

    if SHOW_PLOTS:
        plt.show()
    else:
        plt.close(figure)


# =============================================================
# VARIABLE-PRESSURE PLOTS
# =============================================================

def plot_variable_pressure_before_after(metrics_dataframe):
    """
    Compare variable pressure before and after pressure increase.
    """

    before_condition = (
        "Variable pressure - before increase"
    )

    after_condition = (
        "Variable pressure - after increase"
    )

    muscles = list(EMG_COLUMNS.keys())

    normalized_column = (
        "Overall RMS (V) "
        "(% of without suit)"
    )

    selected_dataframe = metrics_dataframe[
        metrics_dataframe["Condition"].isin([
            before_condition,
            after_condition,
        ])
    ]

    if selected_dataframe.empty:
        return

    pivot_table = selected_dataframe.pivot(
        index="Muscle",
        columns="Condition",
        values=normalized_column,
    )

    pivot_table = pivot_table.reindex(
        index=muscles,
        columns=[
            before_condition,
            after_condition,
        ],
    )

    before_values = pivot_table[
        before_condition
    ].to_numpy(dtype=float)

    after_values = pivot_table[
        after_condition
    ].to_numpy(dtype=float)

    x_positions = np.arange(
        len(muscles)
    )

    bar_width = 0.36

    figure, axis = plt.subplots(
        figsize=(12, 7)
    )

    axis.bar(
        x_positions - bar_width / 2,
        before_values,
        width=bar_width,
        label="Before pressure increase",
    )

    axis.bar(
        x_positions + bar_width / 2,
        after_values,
        width=bar_width,
        label="After pressure increase",
    )

    axis.axhline(
        y=100.0,
        linestyle="--",
        linewidth=1.0,
        label="Without-suit reference",
    )

    axis.set_xticks(
        x_positions
    )

    axis.set_xticklabels(
        muscles
    )

    axis.set_xlabel(
        "Muscle"
    )

    axis.set_ylabel(
        "RMS activity (% of without suit)"
    )

    axis.set_title(
        "Variable pressure: before and after pressure increase"
    )

    axis.legend()

    axis.grid(
        True,
        axis="y",
        alpha=0.3,
    )

    figure.tight_layout()

    figure.savefig(
        OUTPUT_FOLDER
        / "variable_pressure_before_after_RMS.png",
        dpi=FIGURE_DPI,
        bbox_inches="tight",
    )

    if SHOW_PLOTS:
        plt.show()
    else:
        plt.close(figure)


def plot_variable_pressure_envelopes(processed_trials):
    """
    Plot variable-pressure EMG envelopes with a pressure-change marker.
    """

    condition = "Variable pressure"

    if condition not in processed_trials:
        return

    trial = processed_trials[
        condition
    ]

    time = trial["time"]

    muscles = list(
        EMG_COLUMNS.keys()
    )

    pressure_change_time = (
        VARIABLE_PRESSURE_CHANGE_SECONDS
        - TRIM_START_SECONDS
    )

    figure, axes = plt.subplots(
        nrows=6,
        ncols=1,
        figsize=(13, 14),
        sharex=True,
    )

    for axis, muscle in zip(
        axes,
        muscles,
    ):

        envelope = trial[
            "processed"
        ][muscle]["envelope"]

        axis.plot(
            time,
            envelope,
            linewidth=0.8,
            label=f"{muscle} envelope",
        )

        if (
            pressure_change_time >= time[0]
            and pressure_change_time <= time[-1]
        ):

            axis.axvline(
                x=pressure_change_time,
                linestyle="--",
                linewidth=1.3,
                label="Pressure increased",
            )

        axis.set_ylabel(
            f"{muscle}\n(V)"
        )

        axis.grid(
            True,
            alpha=0.3,
        )

        axis.legend(
            loc="upper right"
        )

    axes[-1].set_xlabel(
        "Time after trimming (s)"
    )

    figure.suptitle(
        "Variable-pressure EMG envelopes",
        fontsize=16,
    )

    figure.tight_layout(
        rect=[0, 0, 1, 0.97]
    )

    figure.savefig(
        OUTPUT_FOLDER
        / "variable_pressure_envelopes.png",
        dpi=FIGURE_DPI,
        bbox_inches="tight",
    )

    if SHOW_PLOTS:
        plt.show()
    else:
        plt.close(figure)


def plot_pressure_change_percentage(metrics_dataframe):
    """
    Plot the percentage change in RMS after increasing pressure.
    """

    before_condition = (
        "Variable pressure - before increase"
    )

    after_condition = (
        "Variable pressure - after increase"
    )

    before_dataframe = (
        metrics_dataframe[
            metrics_dataframe["Condition"]
            == before_condition
        ]
        .set_index("Muscle")
    )

    after_dataframe = (
        metrics_dataframe[
            metrics_dataframe["Condition"]
            == after_condition
        ]
        .set_index("Muscle")
    )

    if (
        before_dataframe.empty
        or after_dataframe.empty
    ):
        return

    muscles = list(EMG_COLUMNS.keys())

    percentage_changes = []

    for muscle in muscles:

        before_value = before_dataframe.loc[
            muscle,
            "Overall RMS (V)",
        ]

        after_value = after_dataframe.loc[
            muscle,
            "Overall RMS (V)",
        ]

        if isinstance(before_value, pd.Series):
            before_value = before_value.iloc[0]

        if isinstance(after_value, pd.Series):
            after_value = after_value.iloc[0]

        if (
            not np.isfinite(before_value)
            or before_value == 0
        ):

            percentage_change = np.nan

        else:

            percentage_change = (
                after_value
                - before_value
            ) / before_value * 100.0

        percentage_changes.append(
            percentage_change
        )

    figure, axis = plt.subplots(
        figsize=(10, 6)
    )

    bars = axis.bar(
        muscles,
        percentage_changes,
    )

    axis.axhline(
        y=0.0,
        linewidth=1.0,
    )

    axis.set_xlabel(
        "Muscle"
    )

    axis.set_ylabel(
        "RMS change after pressure increase (%)"
    )

    axis.set_title(
        "Effect of increasing pressure on muscle activity"
    )

    axis.grid(
        True,
        axis="y",
        alpha=0.3,
    )

    for bar, value in zip(
        bars,
        percentage_changes,
    ):

        if np.isfinite(value):

            vertical_alignment = (
                "bottom"
                if value >= 0
                else "top"
            )

            axis.text(
                bar.get_x()
                + bar.get_width() / 2,
                value,
                f"{value:+.1f}%",
                ha="center",
                va=vertical_alignment,
            )

    figure.tight_layout()

    figure.savefig(
        OUTPUT_FOLDER
        / "pressure_increase_percentage_change.png",
        dpi=FIGURE_DPI,
        bbox_inches="tight",
    )

    if SHOW_PLOTS:
        plt.show()
    else:
        plt.close(figure)


# =============================================================
# SUMMARY TABLES
# =============================================================

def create_summary_tables(metrics_dataframe):
    """
    Create absolute and normalized RMS summary tables.
    """

    condition_order = [
        "Without suit",
        "Suit, no actuation",
        "Constant pressure",
        "Variable pressure",
        "Variable pressure - before increase",
        "Variable pressure - after increase",
    ]

    muscles = list(
        EMG_COLUMNS.keys()
    )

    absolute_rms_table = metrics_dataframe.pivot(
        index="Muscle",
        columns="Condition",
        values="Overall RMS (V)",
    )

    normalized_rms_column = (
        "Overall RMS (V) "
        "(% of without suit)"
    )

    normalized_rms_table = metrics_dataframe.pivot(
        index="Muscle",
        columns="Condition",
        values=normalized_rms_column,
    )

    available_conditions = [
        condition
        for condition in condition_order
        if condition in absolute_rms_table.columns
    ]

    absolute_rms_table = absolute_rms_table.reindex(
        index=muscles,
        columns=available_conditions,
    )

    normalized_rms_table = normalized_rms_table.reindex(
        index=muscles,
        columns=available_conditions,
    )

    return (
        absolute_rms_table,
        normalized_rms_table,
    )


def create_pressure_change_table(metrics_dataframe):
    """
    Create a table comparing RMS before and after pressure increase.
    """

    before_condition = (
        "Variable pressure - before increase"
    )

    after_condition = (
        "Variable pressure - after increase"
    )

    before_dataframe = (
        metrics_dataframe[
            metrics_dataframe["Condition"]
            == before_condition
        ]
        .set_index("Muscle")
    )

    after_dataframe = (
        metrics_dataframe[
            metrics_dataframe["Condition"]
            == after_condition
        ]
        .set_index("Muscle")
    )

    rows = []

    for muscle in EMG_COLUMNS:

        if (
            muscle not in before_dataframe.index
            or muscle not in after_dataframe.index
        ):
            continue

        before_rms = before_dataframe.loc[
            muscle,
            "Overall RMS (V)",
        ]

        after_rms = after_dataframe.loc[
            muscle,
            "Overall RMS (V)",
        ]

        if isinstance(before_rms, pd.Series):
            before_rms = before_rms.iloc[0]

        if isinstance(after_rms, pd.Series):
            after_rms = after_rms.iloc[0]

        if (
            not np.isfinite(before_rms)
            or before_rms == 0
        ):

            percentage_change = np.nan

        else:

            percentage_change = (
                after_rms
                - before_rms
            ) / before_rms * 100.0

        rows.append({
            "Muscle": muscle,
            "RMS before increase (V)": before_rms,
            "RMS after increase (V)": after_rms,
            "RMS difference (V)": (
                after_rms - before_rms
            ),
            "Change after increase (%)": percentage_change,
        })

    return pd.DataFrame(rows)


# =============================================================
# MAIN FUNCTION
# =============================================================

def main():
    """
    Run the complete four-condition EMG analysis.
    """

    OUTPUT_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("\n" + "=" * 75)
    print("FOUR-CONDITION EMG ANALYSIS")
    print("=" * 75)

    processed_trials = {}

    # ---------------------------------------------------------
    # Read and process all four CSV files
    # ---------------------------------------------------------

    for condition, filename in FILES.items():

        processed_trials[condition] = (
            process_complete_file(
                condition=condition,
                filename=filename,
            )
        )

    # ---------------------------------------------------------
    # Calculate activity metrics
    # ---------------------------------------------------------

    metrics_dataframe = calculate_all_metrics(
        processed_trials
    )

    metrics_dataframe = normalize_to_without_suit(
        metrics_dataframe
    )

    # ---------------------------------------------------------
    # Create summary tables
    # ---------------------------------------------------------

    (
        absolute_rms_table,
        normalized_rms_table,
    ) = create_summary_tables(
        metrics_dataframe
    )

    pressure_change_table = create_pressure_change_table(
        metrics_dataframe
    )

    # ---------------------------------------------------------
    # Save numerical results as CSV files
    # ---------------------------------------------------------

    metrics_dataframe.to_csv(
        OUTPUT_FOLDER
        / "all_EMG_metrics.csv",
        index=False,
    )

    absolute_rms_table.to_csv(
        OUTPUT_FOLDER
        / "absolute_RMS_summary.csv"
    )

    normalized_rms_table.to_csv(
        OUTPUT_FOLDER
        / "normalized_RMS_summary.csv"
    )

    pressure_change_table.to_csv(
        OUTPUT_FOLDER
        / "variable_pressure_change.csv",
        index=False,
    )

    # ---------------------------------------------------------
    # Save all tables in one Excel workbook
    # ---------------------------------------------------------

    excel_filename = (
        OUTPUT_FOLDER
        / "EMG_analysis_results.xlsx"
    )

    with pd.ExcelWriter(
        excel_filename
    ) as writer:

        metrics_dataframe.to_excel(
            writer,
            sheet_name="All metrics",
            index=False,
        )

        absolute_rms_table.to_excel(
            writer,
            sheet_name="Absolute RMS",
        )

        normalized_rms_table.to_excel(
            writer,
            sheet_name="Normalized RMS",
        )

        pressure_change_table.to_excel(
            writer,
            sheet_name="Pressure change",
            index=False,
        )

    # ---------------------------------------------------------
    # Save processed waveform data
    # ---------------------------------------------------------

    save_processed_signals(
        processed_trials
    )

    # ---------------------------------------------------------
    # Create figures
    # ---------------------------------------------------------

    plot_envelopes_for_each_condition(
        processed_trials
    )

    plot_four_condition_rms(
        metrics_dataframe
    )

    plot_all_muscles_grouped(
        metrics_dataframe
    )

    plot_normalized_rms_heatmap(
        metrics_dataframe
    )

    plot_variable_pressure_before_after(
        metrics_dataframe
    )

    plot_variable_pressure_envelopes(
        processed_trials
    )

    plot_pressure_change_percentage(
        metrics_dataframe
    )

    # Uncomment the following line when you also want individual
    # raw/filtered/envelope plots for every muscle and condition.
    #
    # plot_raw_and_filtered_signals(processed_trials)

    # ---------------------------------------------------------
    # Print key results
    # ---------------------------------------------------------

    print("\n" + "=" * 75)
    print("NORMALIZED RMS RESULTS")
    print("100% = walking without suit")
    print("=" * 75)

    print(
        normalized_rms_table
        .round(2)
        .to_string()
    )

    print("\n" + "=" * 75)
    print("VARIABLE-PRESSURE CHANGE")
    print("=" * 75)

    if pressure_change_table.empty:

        print(
            "The before/after pressure comparison "
            "could not be calculated."
        )

    else:

        print(
            pressure_change_table
            .round(6)
            .to_string(index=False)
        )

    print("\n" + "=" * 75)
    print("ANALYSIS COMPLETED")
    print("=" * 75)

    print(
        f"\nResults saved in:\n"
        f"{OUTPUT_FOLDER.resolve()}"
    )

    print("\nMain output files:")

    print(
        "  all_EMG_metrics.csv"
    )

    print(
        "  absolute_RMS_summary.csv"
    )

    print(
        "  normalized_RMS_summary.csv"
    )

    print(
        "  variable_pressure_change.csv"
    )

    print(
        "  EMG_analysis_results.xlsx"
    )

    print("\nMain figures:")

    print(
        "  four_condition_normalized_RMS.png"
    )

    print(
        "  grouped_normalized_RMS.png"
    )

    print(
        "  normalized_RMS_heatmap.png"
    )

    print(
        "  variable_pressure_before_after_RMS.png"
    )

    print(
        "  variable_pressure_envelopes.png"
    )

    print(
        "  pressure_increase_percentage_change.png"
    )


if __name__ == "__main__":
    main()