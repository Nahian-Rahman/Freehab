

import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# Read CSV
# ==============================
filename = "trial_2_20260629_161821.csv"

df = pd.read_csv(filename)
# If tab-separated, use:
# df = pd.read_csv(filename, sep="\t")

df.columns = df.columns.str.strip()

# ==============================
# Hip trigger: pressure starts after 7° hip change
# ==============================
hip_initial = df["hip x"].iloc[0]

trigger_rows = df.index[abs(df["hip x"] - hip_initial) >= 7]

if len(trigger_rows) == 0:
    print("Hip did not reach 7 degree change.")
    trigger_idx = 0
    trigger_time = df["Time"].iloc[0]
else:
    trigger_idx = trigger_rows[0]
    trigger_time = df.loc[trigger_idx, "Time"]

# ==============================
# Stop condition:
# Sit-to-stand finishes when
# R thigh >= ExR90 OR L thigh >= ExL90
# ==============================
rSitThigh = df["rThighSit"].iloc[0]
lSitThigh = df["lThighSit"].iloc[0]

rStandThigh = df["rThighStand"].iloc[0]
lStandThigh = df["lThighStand"].iloc[0]

ExR90 = rSitThigh + 0.9 * (rStandThigh - rSitThigh)
ExL90 = lSitThigh + 0.9 * (lStandThigh - lSitThigh)

finish_rows = df.index[
    (df.index >= trigger_idx) &
    (
        (df["R thigh"] >= ExR90) |
        (df["L thigh"] >= ExL90)
    )
]

if len(finish_rows) == 0:
    print("Sit-to-stand finish condition was not reached.")
    finish_idx = len(df) - 1
    finish_time = df["Time"].iloc[-1]
else:
    finish_idx = finish_rows[0]
    finish_time = df.loc[finish_idx, "Time"]

# ==============================
# Plot 200 ms after finish condition
# ==============================
plot_end_time = finish_time + 0.2
plot_end_rows = df.index[df["Time"] <= plot_end_time]

if len(plot_end_rows) == 0:
    plot_end_idx = finish_idx
else:
    plot_end_idx = plot_end_rows[-1]

df_plot = df.iloc[:plot_end_idx + 1].copy()

# Plot time starts from zero
df_plot["Plot Time"] = df_plot["Time"] - df_plot["Time"].iloc[0]
t = df_plot["Plot Time"]

trigger_plot_time = trigger_time - df_plot["Time"].iloc[0]
finish_plot_time = finish_time - df_plot["Time"].iloc[0]

# ==============================
# Active STS data only: trigger to 90% finish
# Used for statistics
# ==============================
df_active = df.iloc[trigger_idx:finish_idx + 1].copy()

# ==============================
# Given pressures
# Stored in bar, convert to kPa
# Before hip trigger, set to zero
# ==============================
given_R_up_plot = df_plot["Given Pressure R BAM UP"] * 100
given_R_down_plot = df_plot["Given Pressure R BAM Down"] * 100
given_L_up_plot = df_plot["Given Pressure L BAM UP"] * 100
given_L_down_plot = df_plot["Given Pressure L BAM Down"] * 100

given_R_up_plot[df_plot["Time"] < trigger_time] = 0
given_R_down_plot[df_plot["Time"] < trigger_time] = 0
given_L_up_plot[df_plot["Time"] < trigger_time] = 0
given_L_down_plot[df_plot["Time"] < trigger_time] = 0

# ==============================
# Results
# ==============================
sts_time = finish_time - trigger_time

# Maximum actual pressures only during active STS
max_R_up = df_active["Pressure R BAM UP"].max()
max_R_down = df_active["Pressure R BAM Down"].max()
max_L_up = df_active["Pressure L BAM UP"].max()
max_L_down = df_active["Pressure L BAM Down"].max()

# Maximum forces only during active STS
max_R_force = df_active["R Loadcell"].max()
max_L_force = df_active["L Loadcell"].max()

print("\n========== SIT TO STAND ==========")
print(f"Hip initial value           : {hip_initial:.2f} deg")
print(f"Hip 7° trigger time         : {trigger_time:.3f} s")
print(f"Sit-to-stand finish time    : {finish_time:.3f} s")
print(f"STS duration                : {sts_time:.3f} s")

print("\nThigh calibration values")
print(f"rThighSit                   : {rSitThigh:.2f} deg")
print(f"lThighSit                   : {lSitThigh:.2f} deg")
print(f"rThighStand                 : {rStandThigh:.2f} deg")
print(f"lThighStand                 : {lStandThigh:.2f} deg")

print("\n90% finish thresholds")
print(f"Right thigh 90%             : {ExR90:.2f} deg")
print(f"Left thigh 90%              : {ExL90:.2f} deg")

print("\nMaximum actual pressures during STS (kPa)")
print(f"R UP                        : {max_R_up:.1f}")
print(f"R DOWN                      : {max_R_down:.1f}")
print(f"L UP                        : {max_L_up:.1f}")
print(f"L DOWN                      : {max_L_down:.1f}")

print("\nMaximum forces during STS (N)")
print(f"Right loadcell              : {max_R_force:.1f}")
print(f"Left loadcell               : {max_L_force:.1f}")
print("==================================\n")

# ==============================
# Plot
# ==============================
fig, axs = plt.subplots(3, 1, figsize=(13, 10), sharex=True)

# ---------- Plot 1: All pressures ----------
axs[0].plot(t, given_R_up_plot, "--", label="Given R UP")
axs[0].plot(t, given_R_down_plot, "--", label="Given R Down")
axs[0].plot(t, given_L_up_plot, "--", label="Given L UP")
axs[0].plot(t, given_L_down_plot, "--", label="Given L Down")

axs[0].plot(t, df_plot["Pressure R BAM UP"], label="Actual R UP")
axs[0].plot(t, df_plot["Pressure R BAM Down"], label="Actual R Down")
axs[0].plot(t, df_plot["Pressure L BAM UP"], label="Actual L UP")
axs[0].plot(t, df_plot["Pressure L BAM Down"], label="Actual L Down")

axs[0].axvline(
    trigger_plot_time,
    color="black",
    linestyle=":",
    linewidth=2,
    label="Hip 7° trigger"
)

axs[0].axvline(
    finish_plot_time,
    color="green",
    linestyle="-.",
    linewidth=2,
    label="90% STS finish"
)

pressure_text = (
    f"STS time = {sts_time:.2f} s\n"
    f"Max R UP = {max_R_up:.1f} kPa\n"
    f"Max R Down = {max_R_down:.1f} kPa\n"
    f"Max L UP = {max_L_up:.1f} kPa\n"
    f"Max L Down = {max_L_down:.1f} kPa"
)

axs[0].text(
    0.98,
    0.98,
    pressure_text,
    transform=axs[0].transAxes,
    verticalalignment="top",
    horizontalalignment="right",
    bbox=dict(facecolor="white", alpha=0.8)
)

axs[0].set_ylabel("Pressure (kPa)")
axs[0].set_title("BAM Pressure: Given vs Actual")
axs[0].legend(loc="upper left", ncol=2)
axs[0].grid(True)

# ---------- Plot 2: Thigh angles ----------
axs[1].plot(
    t,
    df_plot["R thigh"],
    color="tab:red",
    linewidth=2,
    label="R thigh"
)

axs[1].plot(
    t,
    df_plot["L thigh"],
    color="tab:blue",
    linewidth=2,
    label="L thigh"
)

# Sitting references
axs[1].axhline(
    rSitThigh,
    color="lightcoral",
    linestyle="-",
    linewidth=1.5,
    label=f"rThighSit = {rSitThigh:.1f}°"
)

axs[1].axhline(
    lSitThigh,
    color="lightskyblue",
    linestyle="-",
    linewidth=1.5,
    label=f"lThighSit = {lSitThigh:.1f}°"
)

# 90% finish thresholds
axs[1].axhline(
    ExR90,
    color="tab:red",
    linestyle="--",
    linewidth=2,
    label=f"R 90% = {ExR90:.1f}°"
)

axs[1].axhline(
    ExL90,
    color="tab:blue",
    linestyle="--",
    linewidth=2,
    label=f"L 90% = {ExL90:.1f}°"
)

# 100% standing references
axs[1].axhline(
    rStandThigh,
    color="darkred",
    linestyle=":",
    linewidth=2,
    label=f"rThighStand = {rStandThigh:.1f}°"
)

axs[1].axhline(
    lStandThigh,
    color="navy",
    linestyle=":",
    linewidth=2,
    label=f"lThighStand = {lStandThigh:.1f}°"
)

# Event markers
axs[1].axvline(
    trigger_plot_time,
    color="black",
    linestyle=":",
    linewidth=2,
    label="Hip 7° trigger"
)

axs[1].axvline(
    finish_plot_time,
    color="green",
    linestyle="-.",
    linewidth=2,
    label="90% STS finish"
)

thigh_text = (
    f"rThighSit = {rSitThigh:.1f}°\n"
    f"lThighSit = {lSitThigh:.1f}°\n"
    f"rThighStand = {rStandThigh:.1f}°\n"
    f"lThighStand = {lStandThigh:.1f}°"
)

axs[1].text(
    0.98,
    0.98,
    thigh_text,
    transform=axs[1].transAxes,
    verticalalignment="top",
    horizontalalignment="right",
    bbox=dict(facecolor="white", alpha=0.8)
)

axs[1].set_ylabel("Thigh angle (deg)")
axs[1].set_title("Right and Left Thigh Angles")
axs[1].legend(loc="upper left", ncol=3)
axs[1].grid(True)

# ---------- Plot 3: Loadcells ----------
axs[2].plot(t, df_plot["R Loadcell"], label="R Loadcell")
axs[2].plot(t, df_plot["L Loadcell"], label="L Loadcell")

axs[2].axvline(
    trigger_plot_time,
    color="black",
    linestyle=":",
    linewidth=2,
    label="Hip 7° trigger"
)

axs[2].axvline(
    finish_plot_time,
    color="green",
    linestyle="-.",
    linewidth=2,
    label="90% STS finish"
)

force_text = (
    f"Max R = {max_R_force:.1f} N\n"
    f"Max L = {max_L_force:.1f} N"
)

axs[2].text(
    0.98,
    0.98,
    force_text,
    transform=axs[2].transAxes,
    verticalalignment="top",
    horizontalalignment="right",
    bbox=dict(facecolor="white", alpha=0.8)
)

axs[2].set_xlabel("Time (s)")
axs[2].set_ylabel("Force (N)")
axs[2].set_title("Loadcell Forces")
axs[2].legend(loc="upper left")
axs[2].grid(True)

plt.tight_layout()
plt.show()


"""
import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# Read CSV
# ==============================
filename = "trial_2_20260629_161821.csv"

df = pd.read_csv(filename)
# If tab-separated, use:
# df = pd.read_csv(filename, sep="\t")

df.columns = df.columns.str.strip()

# ==============================
# Hip trigger: pressure starts after 7° hip change
# ==============================
hip_initial = df["hip x"].iloc[0]

trigger_rows = df.index[abs(df["hip x"] - hip_initial) >= 7]

if len(trigger_rows) == 0:
    print("Hip did not reach 7 degree change.")
    trigger_idx = 0
    trigger_time = df["Time"].iloc[0]
else:
    trigger_idx = trigger_rows[0]
    trigger_time = df.loc[trigger_idx, "Time"]

# ==============================
# Stop condition:
# Sit-to-stand finishes when
# R thigh >= ExR90 OR L thigh >= ExL90
# ==============================
rSitThigh = df["rThighSit"].iloc[0]
lSitThigh = df["lThighSit"].iloc[0]

rStandThigh = df["rThighStand"].iloc[0]
lStandThigh = df["lThighStand"].iloc[0]

ExR90 = rSitThigh + 0.9 * (rStandThigh - rSitThigh)
ExL90 = lSitThigh + 0.9 * (lStandThigh - lSitThigh)

finish_rows = df.index[
    (df.index >= trigger_idx) &
    (
        (df["R thigh"] >= ExR90) |
        (df["L thigh"] >= ExL90)
    )
]

if len(finish_rows) == 0:
    print("Sit-to-stand finish condition was not reached.")
    finish_idx = len(df) - 1
    finish_time = df["Time"].iloc[-1]
else:
    finish_idx = finish_rows[0]
    finish_time = df.loc[finish_idx, "Time"]

# ==============================
# Plot 200 ms after finish condition
# ==============================
plot_end_time = finish_time + 0.2

plot_end_rows = df.index[df["Time"] <= plot_end_time]

if len(plot_end_rows) == 0:
    plot_end_idx = finish_idx
else:
    plot_end_idx = plot_end_rows[-1]

df_plot = df.iloc[:plot_end_idx + 1].copy()

# Plot time starts from zero
df_plot["Plot Time"] = df_plot["Time"] - df_plot["Time"].iloc[0]
t = df_plot["Plot Time"]

trigger_plot_time = trigger_time - df_plot["Time"].iloc[0]
finish_plot_time = finish_time - df_plot["Time"].iloc[0]

# ==============================
# Active data only: trigger to finish
# Used for statistics
# ==============================
df_active = df.iloc[trigger_idx:finish_idx + 1].copy()

# ==============================
# Given pressures
# Stored in bar, convert to kPa
# Before hip trigger, set to zero
# ==============================
given_R_up_plot = df_plot["Given Pressure R BAM UP"] * 100
given_R_down_plot = df_plot["Given Pressure R BAM Down"] * 100
given_L_up_plot = df_plot["Given Pressure L BAM UP"] * 100
given_L_down_plot = df_plot["Given Pressure L BAM Down"] * 100

given_R_up_plot[df_plot["Time"] < trigger_time] = 0
given_R_down_plot[df_plot["Time"] < trigger_time] = 0
given_L_up_plot[df_plot["Time"] < trigger_time] = 0
given_L_down_plot[df_plot["Time"] < trigger_time] = 0

# ==============================
# Results
# ==============================
sts_time = finish_time - trigger_time

# Maximum actual pressures only during active STS
max_R_up = df_active["Pressure R BAM UP"].max()
max_R_down = df_active["Pressure R BAM Down"].max()
max_L_up = df_active["Pressure L BAM UP"].max()
max_L_down = df_active["Pressure L BAM Down"].max()

# Maximum forces only during active STS
max_R_force = df_active["R Loadcell"].max()
max_L_force = df_active["L Loadcell"].max()

print("\n========== SIT TO STAND ==========")
print(f"Hip initial value           : {hip_initial:.2f} deg")
print(f"Hip 7° trigger time         : {trigger_time:.3f} s")
print(f"Sit-to-stand finish time    : {finish_time:.3f} s")
print(f"STS duration                : {sts_time:.3f} s")

print("\n90% finish thresholds")
print(f"Right thigh 90%             : {ExR90:.2f} deg")
print(f"Left thigh 90%              : {ExL90:.2f} deg")

print("\n100% standing references")
print(f"Right thigh stand           : {rStandThigh:.2f} deg")
print(f"Left thigh stand            : {lStandThigh:.2f} deg")

print("\nMaximum actual pressures during STS (kPa)")
print(f"R UP                        : {max_R_up:.1f}")
print(f"R DOWN                      : {max_R_down:.1f}")
print(f"L UP                        : {max_L_up:.1f}")
print(f"L DOWN                      : {max_L_down:.1f}")

print("\nMaximum forces during STS (N)")
print(f"Right loadcell              : {max_R_force:.1f}")
print(f"Left loadcell               : {max_L_force:.1f}")
print("==================================\n")

# ==============================
# Plot
# ==============================
fig, axs = plt.subplots(3, 1, figsize=(13, 10), sharex=True)

# ---------- Plot 1: All pressures ----------
axs[0].plot(t, given_R_up_plot, "--", label="Given R UP")
axs[0].plot(t, given_R_down_plot, "--", label="Given R Down")
axs[0].plot(t, given_L_up_plot, "--", label="Given L UP")
axs[0].plot(t, given_L_down_plot, "--", label="Given L Down")

axs[0].plot(t, df_plot["Pressure R BAM UP"], label="Actual R UP")
axs[0].plot(t, df_plot["Pressure R BAM Down"], label="Actual R Down")
axs[0].plot(t, df_plot["Pressure L BAM UP"], label="Actual L UP")
axs[0].plot(t, df_plot["Pressure L BAM Down"], label="Actual L Down")

axs[0].axvline(trigger_plot_time, linestyle=":", label="Hip 7° trigger")
axs[0].axvline(finish_plot_time, linestyle="-.", label="90% STS finish")

pressure_text = (
    f"STS time = {sts_time:.2f} s\n"
    f"Max R UP = {max_R_up:.1f} kPa\n"
    f"Max R Down = {max_R_down:.1f} kPa\n"
    f"Max L UP = {max_L_up:.1f} kPa\n"
    f"Max L Down = {max_L_down:.1f} kPa"
)

axs[0].text(
    0.98,
    0.98,
    pressure_text,
    transform=axs[0].transAxes,
    verticalalignment="top",
    horizontalalignment="right",
    bbox=dict(facecolor="white", alpha=0.8)
)

axs[0].set_ylabel("Pressure (kPa)")
axs[0].set_title("BAM Pressure: Given vs Actual")
axs[0].legend(loc="upper left", ncol=2)
axs[0].grid(True)

# ---------- Plot 2: Thigh angles ----------
axs[1].plot(t, df_plot["R thigh"], label="R thigh")
axs[1].plot(t, df_plot["L thigh"], label="L thigh")

axs[1].axhline(ExR90, linestyle="--", label="R thigh 90%")
axs[1].axhline(ExL90, linestyle="--", label="L thigh 90%")

axs[1].axhline(rStandThigh, linestyle=":", label="R thigh stand 100%")
axs[1].axhline(lStandThigh, linestyle=":", label="L thigh stand 100%")

axs[1].axvline(trigger_plot_time, linestyle=":", label="Hip 7° trigger")
axs[1].axvline(finish_plot_time, linestyle="-.", label="90% STS finish")

axs[1].set_ylabel("Thigh angle (deg)")
axs[1].set_title("Right and Left Thigh Angles")
axs[1].legend(loc="upper left", ncol=2)
axs[1].grid(True)

# ---------- Plot 3: Loadcells ----------
axs[2].plot(t, df_plot["R Loadcell"], label="R Loadcell")
axs[2].plot(t, df_plot["L Loadcell"], label="L Loadcell")

axs[2].axvline(trigger_plot_time, linestyle=":", label="Hip 7° trigger")
axs[2].axvline(finish_plot_time, linestyle="-.", label="90% STS finish")

force_text = (
    f"Max R = {max_R_force:.1f} N\n"
    f"Max L = {max_L_force:.1f} N"
)

axs[2].text(
    0.98,
    0.98,
    force_text,
    transform=axs[2].transAxes,
    verticalalignment="top",
    horizontalalignment="right",
    bbox=dict(facecolor="white", alpha=0.8)
)

axs[2].set_xlabel("Time (s)")
axs[2].set_ylabel("Force (N)")
axs[2].set_title("Loadcell Forces")
axs[2].legend(loc="upper left")
axs[2].grid(True)

plt.tight_layout()
plt.show()
"""

"""
import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# Read CSV
# ==============================
filename = "trial_2_20260629_161821.csv"

df = pd.read_csv(filename)
# If tab-separated, use:
# df = pd.read_csv(filename, sep="\t")

df.columns = df.columns.str.strip()

# ==============================
# Hip trigger: pressure starts after 7° hip change
# ==============================
hip_initial = df["hip x"].iloc[0]

trigger_rows = df.index[abs(df["hip x"] - hip_initial) >= 7]

if len(trigger_rows) == 0:
    print("Hip did not reach 7 degree change.")
    trigger_idx = 0
    trigger_time = df["Time"].iloc[0]
else:
    trigger_idx = trigger_rows[0]
    trigger_time = df.loc[trigger_idx, "Time"]

# ==============================
# Stop condition:
# Sit-to-stand finishes when
# R thigh >= ExR90 OR L thigh >= ExL90
# ==============================
rSitThigh = df["rThighSit"].iloc[0]
lSitThigh = df["lThighSit"].iloc[0]

rStandThigh = df["rThighStand"].iloc[0]
lStandThigh = df["lThighStand"].iloc[0]

ExR90 = rSitThigh + 0.9 * (rStandThigh - rSitThigh)
ExL90 = lSitThigh + 0.9 * (lStandThigh - lSitThigh)

finish_rows = df.index[
    (df.index >= trigger_idx) &
    (
        (df["R thigh"] >= ExR90) |
        (df["L thigh"] >= ExL90)
    )
]

if len(finish_rows) == 0:
    print("Sit-to-stand finish condition was not reached.")
    finish_idx = len(df) - 1
    finish_time = df["Time"].iloc[-1]
else:
    finish_idx = finish_rows[0]
    finish_time = df.loc[finish_idx, "Time"]

# ==============================
# Crop data after stopping condition
# ==============================
df_plot = df.iloc[:finish_idx + 1].copy()

# Plot time starts from zero
df_plot["Plot Time"] = df_plot["Time"] - df_plot["Time"].iloc[0]
t = df_plot["Plot Time"]

trigger_plot_time = trigger_time - df_plot["Time"].iloc[0]

# ==============================
# Given pressures
# Stored in bar, convert to kPa
# Before hip trigger, set to zero
# ==============================
given_R_up_plot = df_plot["Given Pressure R BAM UP"] * 100
given_R_down_plot = df_plot["Given Pressure R BAM Down"] * 100
given_L_up_plot = df_plot["Given Pressure L BAM UP"] * 100
given_L_down_plot = df_plot["Given Pressure L BAM Down"] * 100

given_R_up_plot[df_plot["Time"] < trigger_time] = 0
given_R_down_plot[df_plot["Time"] < trigger_time] = 0
given_L_up_plot[df_plot["Time"] < trigger_time] = 0
given_L_down_plot[df_plot["Time"] < trigger_time] = 0

# ==============================
# Results
# ==============================
sts_time = finish_time - trigger_time

# Maximum actual pressures only
max_R_up = df_plot["Pressure R BAM UP"].max()
max_R_down = df_plot["Pressure R BAM Down"].max()
max_L_up = df_plot["Pressure L BAM UP"].max()
max_L_down = df_plot["Pressure L BAM Down"].max()

# Maximum forces
max_R_force = df_plot["R Loadcell"].max()
max_L_force = df_plot["L Loadcell"].max()

print("\n========== SIT TO STAND ==========")
print(f"Hip initial value           : {hip_initial:.2f} deg")
print(f"Hip 7° trigger time         : {trigger_time:.3f} s")
print(f"Sit-to-stand finish time    : {finish_time:.3f} s")
print(f"STS duration                : {sts_time:.3f} s")

print("\nMaximum actual pressures (kPa)")
print(f"R UP                        : {max_R_up:.1f}")
print(f"R DOWN                      : {max_R_down:.1f}")
print(f"L UP                        : {max_L_up:.1f}")
print(f"L DOWN                      : {max_L_down:.1f}")

print("\nMaximum forces (N)")
print(f"Right loadcell              : {max_R_force:.1f}")
print(f"Left loadcell               : {max_L_force:.1f}")
print("==================================\n")

# ==============================
# Plot
# ==============================
fig, axs = plt.subplots(3, 1, figsize=(13, 10), sharex=True)

# ---------- Plot 1: Right pressures ----------
axs[0].plot(t, given_R_up_plot, "--", label="Given R UP")
axs[0].plot(t, given_R_down_plot, "--", label="Given R Down")
axs[0].plot(t, df_plot["Pressure R BAM UP"], label="Actual R UP")
axs[0].plot(t, df_plot["Pressure R BAM Down"], label="Actual R Down")

axs[0].axvline(trigger_plot_time, linestyle=":", label="Hip 7° trigger")

pressure_text = (
    f"STS time = {sts_time:.2f} s\n"
    f"Max actual R UP = {max_R_up:.1f} kPa\n"
    f"Max actual R Down = {max_R_down:.1f} kPa\n"
    f"Max actual L UP = {max_L_up:.1f} kPa\n"
    f"Max actual L Down = {max_L_down:.1f} kPa"
)

axs[0].text(
    0.98,
    0.98,
    pressure_text,
    transform=axs[0].transAxes,
    verticalalignment="top",
    horizontalalignment="right",
    bbox=dict(facecolor="white", alpha=0.8)
)

axs[0].set_ylabel("Pressure (kPa)")
axs[0].set_title("Right BAM Pressure: Given vs Actual")
axs[0].legend(loc="upper left")
axs[0].grid(True)

# ---------- Plot 2: Left pressures ----------
axs[1].plot(t, given_L_up_plot, "--", label="Given L UP")
axs[1].plot(t, given_L_down_plot, "--", label="Given L Down")
axs[1].plot(t, df_plot["Pressure L BAM UP"], label="Actual L UP")
axs[1].plot(t, df_plot["Pressure L BAM Down"], label="Actual L Down")

axs[1].axvline(trigger_plot_time, linestyle=":", label="Hip 7° trigger")

axs[1].set_ylabel("Pressure (kPa)")
axs[1].set_title("Left BAM Pressure: Given vs Actual")
axs[1].legend(loc="upper left")
axs[1].grid(True)

# ---------- Plot 3: Loadcells ----------
axs[2].plot(t, df_plot["R Loadcell"], label="R Loadcell")
axs[2].plot(t, df_plot["L Loadcell"], label="L Loadcell")

axs[2].axvline(trigger_plot_time, linestyle=":", label="Hip 7° trigger")

force_text = (
    f"Max R = {max_R_force:.1f} N\n"
    f"Max L = {max_L_force:.1f} N"
)

axs[2].text(
    0.98,
    0.98,
    force_text,
    transform=axs[2].transAxes,
    verticalalignment="top",
    horizontalalignment="right",
    bbox=dict(facecolor="white", alpha=0.8)
)

axs[2].set_xlabel("Time (s)")
axs[2].set_ylabel("Force (N)")
axs[2].set_title("Loadcell Forces")
axs[2].legend(loc="upper left")
axs[2].grid(True)

plt.tight_layout()
plt.show()

"""