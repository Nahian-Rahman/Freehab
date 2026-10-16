import os
import pandas as pd
import matplotlib.pyplot as plt

# =====================================================
# Read CSV
# =====================================================
filename = "trial_2_20260629_161821.csv"

df = pd.read_csv(filename)
df.columns = df.columns.str.strip()

# =====================================================
# Output folder
# =====================================================
#out_dir = "STS_split_analysis"+"_{filename}"
#os.makedirs(out_dir, exist_ok=True)


base_name = os.path.splitext(os.path.basename(filename))[0]
out_dir = f"STS_split_analysis_{base_name}"

os.makedirs(out_dir, exist_ok=True)
# =====================================================
# Threshold
# =====================================================
pressure_start_threshold_bar = 1.15

# =====================================================
# Sitting / Standing reference angles
# =====================================================
rSitThigh = df["rThighSit"].iloc[0]
lSitThigh = df["lThighSit"].iloc[0]
rStandThigh = df["rThighStand"].iloc[0]
lStandThigh = df["lThighStand"].iloc[0]

ExR90 = rSitThigh + 0.9 * (rStandThigh - rSitThigh)
ExL90 = lSitThigh + 0.9 * (lStandThigh - lSitThigh)

# =====================================================
# Detect STS starts
# =====================================================
given_cols = [
    "Given Pressure R BAM UP",
    "Given Pressure R BAM Down",
    "Given Pressure L BAM UP",
    "Given Pressure L BAM Down"
]

given_max_bar = df[given_cols].max(axis=1)

active = given_max_bar >= pressure_start_threshold_bar
start_indices = []

for i in range(1, len(df)):
    if active.iloc[i] and not active.iloc[i - 1]:
        start_indices.append(i)

print(f"Detected {len(start_indices)} sit-to-stand starts")

# =====================================================
# Analysis
# =====================================================
summary = []

for trial_num, start_idx in enumerate(start_indices, start=1):

    start_time = df.loc[start_idx, "Time"]

    # =================================================
    # Finish condition
    # =================================================
    finish_rows = df.index[
        (df.index >= start_idx)
        &
        (
            (df["R thigh"] >= ExR90)
            |
            (df["L thigh"] >= ExL90)
        )
    ]

    if len(finish_rows) == 0:
        print(f"Trial {trial_num}: finish condition not reached")
        continue

    finish_idx = finish_rows[0]
    finish_time = df.loc[finish_idx, "Time"]

    # =================================================
    # Extract trial
    # =================================================
    df_trial = df.iloc[start_idx:finish_idx + 1].copy()

    df_trial["Trial Time"] = (
        df_trial["Time"]
        - df_trial["Time"].iloc[0]
    )

    t = df_trial["Trial Time"]

    sts_time = finish_time - start_time

    # =================================================
    # Pressures
    # =================================================
    given_R_up = df_trial["Given Pressure R BAM UP"] * 100
    given_R_down = df_trial["Given Pressure R BAM Down"] * 100
    given_L_up = df_trial["Given Pressure L BAM UP"] * 100
    given_L_down = df_trial["Given Pressure L BAM Down"] * 100

    max_R_up = df_trial["Pressure R BAM UP"].max()
    max_R_down = df_trial["Pressure R BAM Down"].max()
    max_L_up = df_trial["Pressure L BAM UP"].max()
    max_L_down = df_trial["Pressure L BAM Down"].max()

    # =================================================
    # Loadcells
    # =================================================
    max_R_force = df_trial["R Loadcell"].max()
    max_L_force = df_trial["L Loadcell"].max()

    # =================================================
    # Summary
    # =================================================
    summary.append({
        "Trial": trial_num,
        "Start Time (s)": start_time,
        "Finish Time (s)": finish_time,
        "STS Time (s)": sts_time,
        "Max Actual R UP (kPa)": max_R_up,
        "Max Actual R Down (kPa)": max_R_down,
        "Max Actual L UP (kPa)": max_L_up,
        "Max Actual L Down (kPa)": max_L_down,
        "Max R Loadcell (N)": max_R_force,
        "Max L Loadcell (N)": max_L_force,
    })

    # =================================================
    # Save individual trial
    # =================================================
    trial_csv = os.path.join(
        out_dir,
        f"trial_{trial_num:02d}.csv"
    )

    df_trial.to_csv(trial_csv, index=False)

    # =================================================
    # Plot
    # =================================================
    fig, axs = plt.subplots(
        3,
        1,
        figsize=(14, 11),
        sharex=True
    )

    trial_start_x = 0
    trial_end_x = sts_time

    # =================================================
    # Plot 1
    # All pressures
    # =================================================
    axs[0].plot(
        t,
        given_R_up,
        '--',
        linewidth=2,
        label='Given R UP'
    )

    axs[0].plot(
        t,
        given_R_down,
        '--',
        linewidth=2,
        label='Given R Down'
    )

    axs[0].plot(
        t,
        given_L_up,
        '--',
        linewidth=2,
        label='Given L UP'
    )

    axs[0].plot(
        t,
        given_L_down,
        '--',
        linewidth=2,
        label='Given L Down'
    )

    axs[0].plot(
        t,
        df_trial["Pressure R BAM UP"],
        linewidth=2,
        label='Actual R UP'
    )

    axs[0].plot(
        t,
        df_trial["Pressure R BAM Down"],
        linewidth=2,
        label='Actual R Down'
    )

    axs[0].plot(
        t,
        df_trial["Pressure L BAM UP"],
        linewidth=2,
        label='Actual L UP'
    )

    axs[0].plot(
        t,
        df_trial["Pressure L BAM Down"],
        linewidth=2,
        label='Actual L Down'
    )

    # vertical lines
    axs[0].axvline(
        trial_start_x,
        color='black',
        linestyle='--',
        linewidth=2,
        label='Start'
    )

    axs[0].axvline(
        trial_end_x,
        color='red',
        linestyle='--',
        linewidth=2,
        label='Finish'
    )

    pressure_text = (
        f"STS={sts_time:.2f}s\n"
        f"RUP={max_R_up:.1f}\n"
        f"RDN={max_R_down:.1f}\n"
        f"LUP={max_L_up:.1f}\n"
        f"LDN={max_L_down:.1f}"
    )

    axs[0].text(
        0.98,
        0.98,
        pressure_text,
        transform=axs[0].transAxes,
        va='top',
        ha='right',
        bbox=dict(
            facecolor='white',
            alpha=0.8
        )
    )

    axs[0].set_ylabel("Pressure (kPa)")
    axs[0].set_title(
        f"Trial {trial_num}: All Pressures"
    )
    axs[0].legend(
        loc='upper left',
        ncol=2
    )
    axs[0].grid(True)

    # =================================================
    # Plot 2
    # Angles
    # =================================================
    axs[1].plot(
        t,
        df_trial["R thigh"],
        linewidth=2,
        label='R thigh'
    )

    axs[1].plot(
        t,
        df_trial["L thigh"],
        linewidth=2,
        label='L thigh'
    )

    axs[1].axhline(
        rSitThigh,
        linestyle='--',
        linewidth=1.5,
        label=f'rThighSit={rSitThigh:.1f}'
    )

    axs[1].axhline(
        lSitThigh,
        linestyle='--',
        linewidth=1.5,
        label=f'lThighSit={lSitThigh:.1f}'
    )

    axs[1].axhline(
        rStandThigh,
        linestyle=':',
        linewidth=2,
        label=f'rThighStand={rStandThigh:.1f}'
    )

    axs[1].axhline(
        lStandThigh,
        linestyle=':',
        linewidth=2,
        label=f'lThighStand={lStandThigh:.1f}'
    )

    axs[1].axhline(
        ExR90,
        linestyle='-.',
        linewidth=2,
        label=f'R90={ExR90:.1f}'
    )

    axs[1].axhline(
        ExL90,
        linestyle='-.',
        linewidth=2,
        label=f'L90={ExL90:.1f}'
    )

    # vertical lines
    axs[1].axvline(
        trial_start_x,
        color='black',
        linestyle='--',
        linewidth=2,
        label='Start'
    )

    axs[1].axvline(
        trial_end_x,
        color='red',
        linestyle='--',
        linewidth=2,
        label='Finish'
    )

    angle_text = (
        f"rSit={rSitThigh:.1f}\n"
        f"lSit={lSitThigh:.1f}\n"
        f"rStand={rStandThigh:.1f}\n"
        f"lStand={lStandThigh:.1f}"
    )

    axs[1].text(
        0.98,
        0.98,
        angle_text,
        transform=axs[1].transAxes,
        va='top',
        ha='right',
        bbox=dict(
            facecolor='white',
            alpha=0.8
        )
    )

    axs[1].set_ylabel(
        "Thigh Angle (deg)"
    )

    axs[1].set_title(
        f"Trial {trial_num}: Thigh Angles"
    )

    axs[1].legend(
        loc='upper left',
        ncol=2
    )

    axs[1].grid(True)

    # =================================================
    # Plot 3
    # Loadcells
    # =================================================
    axs[2].plot(
        t,
        df_trial["R Loadcell"],
        linewidth=2,
        label='R Loadcell'
    )

    axs[2].plot(
        t,
        df_trial["L Loadcell"],
        linewidth=2,
        label='L Loadcell'
    )

    # vertical lines
    axs[2].axvline(
        trial_start_x,
        color='black',
        linestyle='--',
        linewidth=2,
        label='Start'
    )

    axs[2].axvline(
        trial_end_x,
        color='red',
        linestyle='--',
        linewidth=2,
        label='Finish'
    )

    force_text = (
        f"Max R={max_R_force:.1f} N\n"
        f"Max L={max_L_force:.1f} N"
    )

    axs[2].text(
        0.98,
        0.98,
        force_text,
        transform=axs[2].transAxes,
        va='top',
        ha='right',
        bbox=dict(
            facecolor='white',
            alpha=0.8
        )
    )

    axs[2].set_xlabel(
        "Time from pressure start (s)"
    )

    axs[2].set_ylabel(
        "Force (N)"
    )

    axs[2].set_title(
        f"Trial {trial_num}: Loadcell Forces"
    )

    axs[2].legend(
        loc='upper left'
    )

    axs[2].grid(True)

    plt.tight_layout()

    fig_path = os.path.join(
        out_dir,
        f"trial_{trial_num:02d}.png"
    )

    plt.savefig(
        fig_path,
        dpi=300
    )

    plt.close()

# =====================================================
# Summary
# =====================================================
summary_df = pd.DataFrame(summary)

avg_sts = summary_df["STS Time (s)"].mean()

average_row = {
    "Trial": "Average",
    "Start Time (s)": "",
    "Finish Time (s)": "",
    "STS Time (s)": avg_sts,
    "Max Actual R UP (kPa)": "",
    "Max Actual R Down (kPa)": "",
    "Max Actual L UP (kPa)": "",
    "Max Actual L Down (kPa)": "",
    "Max R Loadcell (N)": "",
    "Max L Loadcell (N)": ""
}

summary_df = pd.concat(
    [
        summary_df,
        pd.DataFrame([average_row])
    ],
    ignore_index=True
)

summary_csv = os.path.join(
    out_dir,
    "sts_summary.csv"
)

summary_xlsx = os.path.join(
    out_dir,
    "sts_summary.xlsx"
)

summary_df.to_csv(
    summary_csv,
    index=False
)

summary_df.to_excel(
    summary_xlsx,
    index=False
)

print("\n========== SUMMARY ==========")
print(summary_df)

print(
    f"\nAverage STS time = {avg_sts:.2f} s"
)

print(
    f"\nSaved results in folder: {out_dir}"
)





"""
import os
import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# Read CSV
# ==============================
filename = "trial_2_20260629_161821.csv"

df = pd.read_csv(filename)
df.columns = df.columns.str.strip()

# ==============================
# Output folder
# ==============================
out_dir = "STS_split_analysis"
os.makedirs(out_dir, exist_ok=True)

# ==============================
# Thresholds
# ==============================
pressure_start_threshold_bar = 1.15

# ==============================
# Sitting / standing thigh values
# ==============================
rSitThigh = df["rThighSit"].iloc[0]
lSitThigh = df["lThighSit"].iloc[0]
rStandThigh = df["rThighStand"].iloc[0]
lStandThigh = df["lThighStand"].iloc[0]

ExR90 = rSitThigh + 0.9 * (rStandThigh - rSitThigh)
ExL90 = lSitThigh + 0.9 * (lStandThigh - lSitThigh)

# ==============================
# Detect trial starts
# ==============================
given_cols = [
    "Given Pressure R BAM UP",
    "Given Pressure R BAM Down",
    "Given Pressure L BAM UP",
    "Given Pressure L BAM Down"
]

given_max_bar = df[given_cols].max(axis=1)
active = given_max_bar >= pressure_start_threshold_bar

start_indices = []

for i in range(1, len(df)):
    if active.iloc[i] and not active.iloc[i - 1]:
        start_indices.append(i)

print(f"Detected {len(start_indices)} sit-to-stand starts")

# ==============================
# Analyse each trial
# ==============================
summary = []

for trial_num, start_idx in enumerate(start_indices, start=1):

    start_time = df.loc[start_idx, "Time"]

    finish_rows = df.index[
        (df.index >= start_idx) &
        (
            (df["R thigh"] >= ExR90) |
            (df["L thigh"] >= ExL90)
        )
    ]

    if len(finish_rows) == 0:
        print(f"Trial {trial_num}: finish condition not reached")
        continue

    finish_idx = finish_rows[0]
    finish_time = df.loc[finish_idx, "Time"]

    df_trial = df.iloc[start_idx:finish_idx + 1].copy()
    df_trial["Trial Time"] = df_trial["Time"] - df_trial["Time"].iloc[0]

    t = df_trial["Trial Time"]
    sts_time = finish_time - start_time

    # ==============================
    # Pressures
    # Given pressures: bar to kPa
    # ==============================
    given_R_up = df_trial["Given Pressure R BAM UP"] * 100
    given_R_down = df_trial["Given Pressure R BAM Down"] * 100
    given_L_up = df_trial["Given Pressure L BAM UP"] * 100
    given_L_down = df_trial["Given Pressure L BAM Down"] * 100

    max_R_up = df_trial["Pressure R BAM UP"].max()
    max_R_down = df_trial["Pressure R BAM Down"].max()
    max_L_up = df_trial["Pressure L BAM UP"].max()
    max_L_down = df_trial["Pressure L BAM Down"].max()

    # ==============================
    # Loadcells
    # ==============================
    max_R_force = df_trial["R Loadcell"].max()
    max_L_force = df_trial["L Loadcell"].max()

    summary.append({
        "Trial": trial_num,
        "Start Time (s)": start_time,
        "Finish Time (s)": finish_time,
        "STS Time (s)": sts_time,
        "Max Actual R UP (kPa)": max_R_up,
        "Max Actual R Down (kPa)": max_R_down,
        "Max Actual L UP (kPa)": max_L_up,
        "Max Actual L Down (kPa)": max_L_down,
        "Max R Loadcell (N)": max_R_force,
        "Max L Loadcell (N)": max_L_force,
    })

    # Save trial CSV
    trial_csv = os.path.join(out_dir, f"trial_{trial_num:02d}.csv")
    df_trial.to_csv(trial_csv, index=False)

    # ==============================
    # Plot each trial
    # ==============================
    fig, axs = plt.subplots(3, 1, figsize=(14, 11), sharex=True)

    # ==================================================
    # Plot 1: All pressures merged
    # ==================================================
    axs[0].plot(t, given_R_up, "--", linewidth=2, label="Given R UP")
    axs[0].plot(t, given_R_down, "--", linewidth=2, label="Given R Down")
    axs[0].plot(t, given_L_up, "--", linewidth=2, label="Given L UP")
    axs[0].plot(t, given_L_down, "--", linewidth=2, label="Given L Down")

    axs[0].plot(t, df_trial["Pressure R BAM UP"], linewidth=2, label="Actual R UP")
    axs[0].plot(t, df_trial["Pressure R BAM Down"], linewidth=2, label="Actual R Down")
    axs[0].plot(t, df_trial["Pressure L BAM UP"], linewidth=2, label="Actual L UP")
    axs[0].plot(t, df_trial["Pressure L BAM Down"], linewidth=2, label="Actual L Down")

    pressure_text = (
        f"STS time = {sts_time:.2f} s\n"
        f"Max R UP = {max_R_up:.1f} kPa\n"
        f"Max R Down = {max_R_down:.1f} kPa\n"
        f"Max L UP = {max_L_up:.1f} kPa\n"
        f"Max L Down = {max_L_down:.1f} kPa"
    )

    axs[0].text(
        0.98, 0.98, pressure_text,
        transform=axs[0].transAxes,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(facecolor="white", alpha=0.85)
    )

    axs[0].set_ylabel("Pressure (kPa)")
    axs[0].set_title(f"Trial {trial_num}: All BAM Pressures")
    axs[0].legend(loc="upper left", ncol=2)
    axs[0].grid(True)

    # ==================================================
    # Plot 2: Angles
    # ==================================================
    axs[1].plot(t, df_trial["R thigh"], linewidth=2, label="R thigh")
    axs[1].plot(t, df_trial["L thigh"], linewidth=2, label="L thigh")

    axs[1].axhline(rSitThigh, linestyle="--", linewidth=1.5, label=f"rThighSit = {rSitThigh:.1f}")
    axs[1].axhline(lSitThigh, linestyle="--", linewidth=1.5, label=f"lThighSit = {lSitThigh:.1f}")
    axs[1].axhline(rStandThigh, linestyle=":", linewidth=2, label=f"rThighStand = {rStandThigh:.1f}")
    axs[1].axhline(lStandThigh, linestyle=":", linewidth=2, label=f"lThighStand = {lStandThigh:.1f}")

    axs[1].axhline(ExR90, linestyle="-.", linewidth=1.5, label=f"R 90% = {ExR90:.1f}")
    axs[1].axhline(ExL90, linestyle="-.", linewidth=1.5, label=f"L 90% = {ExL90:.1f}")

    axs[1].axvline(sts_time, linestyle="--", linewidth=1.5, label=f"tstand = {sts_time:.2f}s")

    angle_text = (
        f"rThighSit = {rSitThigh:.1f}\n"
        f"lThighSit = {lSitThigh:.1f}\n"
        f"rThighStand = {rStandThigh:.1f}\n"
        f"lThighStand = {lStandThigh:.1f}"
    )

    axs[1].text(
        0.98, 0.98, angle_text,
        transform=axs[1].transAxes,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(facecolor="white", alpha=0.85)
    )

    axs[1].set_ylabel("Thigh Angle (deg)")
    axs[1].set_title(f"Trial {trial_num}: Thigh Angles")
    axs[1].legend(loc="upper left", ncol=2)
    axs[1].grid(True)

    # ==================================================
    # Plot 3: Loadcells same as before
    # ==================================================
    axs[2].plot(t, df_trial["R Loadcell"], linewidth=2, label="R Loadcell")
    axs[2].plot(t, df_trial["L Loadcell"], linewidth=2, label="L Loadcell")

    force_text = (
        f"Max R = {max_R_force:.1f} N\n"
        f"Max L = {max_L_force:.1f} N"
    )

    axs[2].text(
        0.98, 0.98, force_text,
        transform=axs[2].transAxes,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(facecolor="white", alpha=0.85)
    )

    axs[2].set_xlabel("Time from pressure start (s)")
    axs[2].set_ylabel("Force (N)")
    axs[2].set_title(f"Trial {trial_num}: Loadcell Forces")
    axs[2].legend(loc="upper left")
    axs[2].grid(True)

    plt.tight_layout()

    fig_path = os.path.join(out_dir, f"trial_{trial_num:02d}.png")
    plt.savefig(fig_path, dpi=300)
    plt.close()

# ==============================
# Save summary
# ==============================
summary_df = pd.DataFrame(summary)

if len(summary_df) > 0:
    average_sts_time = summary_df["STS Time (s)"].mean()
else:
    average_sts_time = None

average_row = {
    "Trial": "Average",
    "Start Time (s)": "",
    "Finish Time (s)": "",
    "STS Time (s)": average_sts_time,
    "Max Actual R UP (kPa)": "",
    "Max Actual R Down (kPa)": "",
    "Max Actual L UP (kPa)": "",
    "Max Actual L Down (kPa)": "",
    "Max R Loadcell (N)": "",
    "Max L Loadcell (N)": "",
}

summary_df_with_avg = pd.concat(
    [summary_df, pd.DataFrame([average_row])],
    ignore_index=True
)

summary_csv = os.path.join(out_dir, "sts_summary.csv")
summary_xlsx = os.path.join(out_dir, "sts_summary.xlsx")

summary_df_with_avg.to_csv(summary_csv, index=False)
summary_df_with_avg.to_excel(summary_xlsx, index=False)

print("\n========== SUMMARY ==========")
print(summary_df_with_avg)

if average_sts_time is not None:
    print(f"\nAverage STS time = {average_sts_time:.2f} s")

print(f"\nSaved results in folder: {out_dir}")

"""

"""
import os
import pandas as pd
import matplotlib.pyplot as plt

filename = "trial_2_20260629_161821.csv"
df = pd.read_csv(filename)
df.columns = df.columns.str.strip()

# ==============================
# Output folder
# ==============================
out_dir = "STS_split_analysis"
os.makedirs(out_dir, exist_ok=True)

# ==============================
# Thresholds
# ==============================
pressure_start_threshold_bar = 1.15   # detects 1.2 bar command robustly

rSitThigh = df["rThighSit"].iloc[0]
lSitThigh = df["lThighSit"].iloc[0]
rStandThigh = df["rThighStand"].iloc[0]
lStandThigh = df["lThighStand"].iloc[0]

ExR90 = rSitThigh + 0.9 * (rStandThigh - rSitThigh)
ExL90 = lSitThigh + 0.9 * (lStandThigh - lSitThigh)

# ==============================
# Detect trial starts
# Any given pressure reaches about 1.2 bar
# ==============================
given_cols = [
    "Given Pressure R BAM UP",
    "Given Pressure R BAM Down",
    "Given Pressure L BAM UP",
    "Given Pressure L BAM Down"
]

given_max_bar = df[given_cols].max(axis=1)

active = given_max_bar >= pressure_start_threshold_bar
start_indices = []

for i in range(1, len(df)):
    if active.iloc[i] and not active.iloc[i - 1]:
        start_indices.append(i)

print(f"Detected {len(start_indices)} sit-to-stand starts")

# ==============================
# Analyse each trial
# ==============================
summary = []

for trial_num, start_idx in enumerate(start_indices, start=1):

    start_time = df.loc[start_idx, "Time"]

    # End condition: same as previous
    finish_rows = df.index[
        (df.index >= start_idx) &
        (
            (df["R thigh"] >= ExR90) |
            (df["L thigh"] >= ExL90)
        )
    ]

    if len(finish_rows) == 0:
        print(f"Trial {trial_num}: finish condition not reached")
        continue

    finish_idx = finish_rows[0]
    finish_time = df.loc[finish_idx, "Time"]

    # Trial data only: start to finish
    df_trial = df.iloc[start_idx:finish_idx + 1].copy()
    df_trial["Trial Time"] = df_trial["Time"] - df_trial["Time"].iloc[0]
    t = df_trial["Trial Time"]

    sts_time = finish_time - start_time

    # Given pressures: bar to kPa
    given_R_up = df_trial["Given Pressure R BAM UP"] * 100
    given_R_down = df_trial["Given Pressure R BAM Down"] * 100
    given_L_up = df_trial["Given Pressure L BAM UP"] * 100
    given_L_down = df_trial["Given Pressure L BAM Down"] * 100

    # Actual pressure maxima
    max_R_up = df_trial["Pressure R BAM UP"].max()
    max_R_down = df_trial["Pressure R BAM Down"].max()
    max_L_up = df_trial["Pressure L BAM UP"].max()
    max_L_down = df_trial["Pressure L BAM Down"].max()

    # Loadcell maxima
    max_R_force = df_trial["R Loadcell"].max()
    max_L_force = df_trial["L Loadcell"].max()

    summary.append({
        "Trial": trial_num,
        "Start Time (s)": start_time,
        "Finish Time (s)": finish_time,
        "STS Time (s)": sts_time,
        "Max Actual R UP (kPa)": max_R_up,
        "Max Actual R Down (kPa)": max_R_down,
        "Max Actual L UP (kPa)": max_L_up,
        "Max Actual L Down (kPa)": max_L_down,
        "Max R Loadcell (N)": max_R_force,
        "Max L Loadcell (N)": max_L_force,
    })

    # Save trial CSV
    trial_csv = os.path.join(out_dir, f"trial_{trial_num:02d}.csv")
    df_trial.to_csv(trial_csv, index=False)

    # ==============================
    # Plot each trial
    # ==============================
    fig, axs = plt.subplots(3, 1, figsize=(13, 10), sharex=True)

    # Plot 1: right pressure
    axs[0].plot(t, given_R_up, "--", label="Given R UP")
    axs[0].plot(t, given_R_down, "--", label="Given R Down")
    axs[0].plot(t, df_trial["Pressure R BAM UP"], label="Actual R UP")
    axs[0].plot(t, df_trial["Pressure R BAM Down"], label="Actual R Down")

    pressure_text = (
        f"STS time = {sts_time:.2f} s\n"
        f"Max R UP = {max_R_up:.1f} kPa\n"
        f"Max R Down = {max_R_down:.1f} kPa\n"
        f"Max L UP = {max_L_up:.1f} kPa\n"
        f"Max L Down = {max_L_down:.1f} kPa"
    )

    axs[0].text(
        0.98, 0.98, pressure_text,
        transform=axs[0].transAxes,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(facecolor="white", alpha=0.8)
    )

    axs[0].set_ylabel("Pressure (kPa)")
    axs[0].set_title(f"Trial {trial_num}: Right BAM Pressure")
    axs[0].legend(loc="upper left")
    axs[0].grid(True)

    # Plot 2: left pressure
    axs[1].plot(t, given_L_up, "--", label="Given L UP")
    axs[1].plot(t, given_L_down, "--", label="Given L Down")
    axs[1].plot(t, df_trial["Pressure L BAM UP"], label="Actual L UP")
    axs[1].plot(t, df_trial["Pressure L BAM Down"], label="Actual L Down")

    axs[1].set_ylabel("Pressure (kPa)")
    axs[1].set_title(f"Trial {trial_num}: Left BAM Pressure")
    axs[1].legend(loc="upper left")
    axs[1].grid(True)

    # Plot 3: loadcells
    axs[2].plot(t, df_trial["R Loadcell"], label="R Loadcell")
    axs[2].plot(t, df_trial["L Loadcell"], label="L Loadcell")

    force_text = (
        f"Max R = {max_R_force:.1f} N\n"
        f"Max L = {max_L_force:.1f} N"
    )

    axs[2].text(
        0.98, 0.98, force_text,
        transform=axs[2].transAxes,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(facecolor="white", alpha=0.8)
    )

    axs[2].set_xlabel("Time from pressure start (s)")
    axs[2].set_ylabel("Force (N)")
    axs[2].set_title(f"Trial {trial_num}: Loadcell Forces")
    axs[2].legend(loc="upper left")
    axs[2].grid(True)

    plt.tight_layout()

    fig_path = os.path.join(out_dir, f"trial_{trial_num:02d}.png")
    plt.savefig(fig_path, dpi=300)
    plt.close()

# ==============================
# Save summary
# ==============================
summary_df = pd.DataFrame(summary)

summary_csv = os.path.join(out_dir, "sts_summary.csv")
summary_xlsx = os.path.join(out_dir, "sts_summary.xlsx")

summary_df.to_csv(summary_csv, index=False)
summary_df.to_excel(summary_xlsx, index=False)

print("\n========== SUMMARY ==========")
print(summary_df)
print(f"\nSaved results in folder: {out_dir}")

""" 