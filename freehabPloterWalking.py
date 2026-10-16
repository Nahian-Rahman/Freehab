import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# Read CSV
# ==============================
filename = "trial_1_20260703_102256.csv"

df = pd.read_csv(filename)
# If tab-separated:
# df = pd.read_csv(filename, sep="\t")

df.columns = df.columns.str.strip()

# ==============================
# Time
# ==============================
t = df["Time"] - df["Time"].iloc[0]

# ==============================
# Given pressures
# Stored in bar -> convert to kPa
# ==============================
given_R_up = df["Given Pressure R BAM UP"] * 100
given_R_down = df["Given Pressure R BAM Down"] * 100

given_L_up = df["Given Pressure L BAM UP"] * 100
given_L_down = df["Given Pressure L BAM Down"] * 100

# ==============================
# Create figure
# ==============================
fig, axs = plt.subplots(
    5,
    1,
    figsize=(15, 14),
    sharex=True
)

# ==========================================================
# Plot 1 : Right pressures
# ==========================================================
axs[0].plot(
    t,
    given_R_up,
    "--",
    label="Given R UP"
)

axs[0].plot(
    t,
    given_R_down,
    "--",
    label="Given R Down"
)

axs[0].plot(
    t,
    df["Pressure R BAM UP"],
    label="Actual R UP"
)

axs[0].plot(
    t,
    df["Pressure R BAM Down"],
    label="Actual R Down"
)

axs[0].set_ylabel("Pressure (kPa)")
axs[0].set_title(
    "Right BAM Pressure: Given vs Actual"
)
axs[0].legend(loc="upper right")
axs[0].grid(True)

# ==========================================================
# Plot 2 : Right gait timing
# ==========================================================
axs[1].step(
    t,
    df["heelR"],
    where="post",
    label="heelR"
)

#axs[1].plot(
 #   t,
 #   df["HeelRp"],
  #  label="HeelRp"
#)

#axs[1].plot(
 #   t,
  #  df["supportTimeR"],
  #  label="supportTimeR"
#)

#axs[1].plot(
 #   t,
  #  df["unsupportTimeR"],
   # label="unsupportTimeR"
#)

axs[1].set_ylabel("Time (s)")
axs[1].set_title(
    "Right Heel Strike and Timing"
)
axs[1].legend(loc="upper right")
axs[1].grid(True)

# ==========================================================
# Plot 3 : Left pressures
# ==========================================================
axs[2].plot(
    t,
    given_L_up,
    "--",
    label="Given L UP"
)

axs[2].plot(
    t,
    given_L_down,
    "--",
    label="Given L Down"
)

axs[2].plot(
    t,
    df["Pressure L BAM UP"],
    label="Actual L UP"
)

axs[2].plot(
    t,
    df["Pressure L BAM Down"],
    label="Actual L Down"
)

axs[2].set_ylabel("Pressure (kPa)")
axs[2].set_title(
    "Left BAM Pressure: Given vs Actual"
)
axs[2].legend(loc="upper right")
axs[2].grid(True)

# ==========================================================
# Plot 4 : Left gait timing
# ==========================================================
axs[3].step(
    t,
    df["heelL"],
    where="post",
    label="heelL"
)

#axs[3].plot(
 #   t,
  #  df["HeelLp"],
   # label="HeelLp"
#)

#axs[3].plot(
 #   t,
  #  df["supportTimeL"],
   # label="supportTimeL"
#)

#axs[3].plot(
 #   t,
  #  df["unsupportTimeL"],
   # label="unsupportTimeL"
#)

axs[3].set_ylabel("Time (s)")
axs[3].set_title(
    "Left Heel Strike and Timing"
)
axs[3].legend(loc="upper right")
axs[3].grid(True)
# ==========================================================
# Plot 5 : Loadcell forces
# ==========================================================
axs[4].plot(
    t,
    df["R Loadcell"],
    label="R Loadcell"
)

axs[4].plot(
    t,
    df["L Loadcell"],
    label="L Loadcell"
)

axs[4].set_ylabel("Force (N)")
axs[4].set_xlabel("Time (s)")
axs[4].set_title(
    "Loadcell Forces"
)
axs[4].legend(loc="upper right")
axs[4].grid(True)
plt.tight_layout()
plt.show()

"""
import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# Read CSV
# ==============================
filename = "trial_22_20260626_114618.csv"

df = pd.read_csv(filename)
# If tab-separated, use:
# df = pd.read_csv(filename, sep="\t")

df.columns = df.columns.str.strip()

# Time starts from 0
t = df["Time"] - df["Time"].iloc[0]

# ==============================
# Given pressures
# Stored in bar, convert to kPa
# Actual pressures are already in kPa
# ==============================
given_R_up = df["Given Pressure R BAM UP"] * 100
given_R_down = df["Given Pressure R BAM Down"] * 100

given_L_up = df["Given Pressure L BAM UP"] * 100
given_L_down = df["Given Pressure L BAM Down"] * 100

# ==============================
# Plot whole walking data
# ==============================
fig, axs = plt.subplots(4, 1, figsize=(15, 12), sharex=True)

# ==========================================================
# Plot 1: Right pressures
# ==========================================================
axs[0].plot(t, given_R_up, "--", label="Given R UP")
axs[0].plot(t, given_R_down, "--", label="Given R Down")
axs[0].plot(t, df["Pressure R BAM UP"], label="Actual R UP")
axs[0].plot(t, df["Pressure R BAM Down"], label="Actual R Down")

axs[0].set_ylabel("Pressure (kPa)")
axs[0].set_title("Right BAM Pressure: Given vs Actual")
axs[0].legend(loc="upper right")
axs[0].grid(True)

# ==========================================================
# Plot 2: Right heel strike + timing variables
# ==========================================================
axs[1].step(t, df["heelR"], where="post", label="Right Heel Strike")
axs[1].plot(t, df["HeelRp"], label="HeelRp")
axs[1].plot(t, df["supportTimeR"], label="supportTimeR")
axs[1].plot(t, df["unsupportTimeR"], label="unsupportTimeR")

axs[1].set_ylabel("Value / Time (s)")
axs[1].set_title("Right Heel Strike and Timing")
axs[1].legend(loc="upper right")
axs[1].grid(True)

# ==========================================================
# Plot 3: Left pressures
# ==========================================================
axs[2].plot(t, given_L_up, "--", label="Given L UP")
axs[2].plot(t, given_L_down, "--", label="Given L Down")
axs[2].plot(t, df["Pressure L BAM UP"], label="Actual L UP")
axs[2].plot(t, df["Pressure L BAM Down"], label="Actual L Down")

axs[2].set_ylabel("Pressure (kPa)")
axs[2].set_title("Left BAM Pressure: Given vs Actual")
axs[2].legend(loc="upper right")
axs[2].grid(True)

# ==========================================================
# Plot 4: Left heel strike + timing variables
# ==========================================================
axs[3].step(t, df["heelL"], where="post", label="Left Heel Strike")
axs[3].plot(t, df["HeelLp"], label="HeelLp")
axs[3].plot(t, df["supportTimeL"], label="supportTimeL")
axs[3].plot(t, df["unsupportTimeL"], label="unsupportTimeL")

axs[3].set_ylabel("Value / Time (s)")
axs[3].set_xlabel("Time (s)")
axs[3].set_title("Left Heel Strike and Timing")
axs[3].legend(loc="upper right")
axs[3].grid(True)

plt.tight_layout()
plt.show()
"""


"""
import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# Read CSV
# ==============================
filename = "trial_22_20260626_114618.csv"

df = pd.read_csv(filename)
# If tab-separated, use:
# df = pd.read_csv(filename, sep="\t")

df.columns = df.columns.str.strip()

# Time
t = df["Time"] - df["Time"].iloc[0]

# ==============================
# Given pressures
# Stored in bar, convert to kPa
# Actual pressures are already in kPa
# ==============================

given_R_up = df["Given Pressure R BAM UP"] * 100
given_R_down = df["Given Pressure R BAM Down"] * 100

given_L_up = df["Given Pressure L BAM UP"] * 100
given_L_down = df["Given Pressure L BAM Down"] * 100

# ==============================
# Plot whole walking data
# ==============================
fig, axs = plt.subplots(4, 1, figsize=(14, 11), sharex=True)

# ---------- Plot 1: Right pressures ----------
axs[0].plot(t, given_R_up, "--", label="Given R UP")
axs[0].plot(t, given_R_down, "--", label="Given R Down")
axs[0].plot(t, df["Pressure R BAM UP"], label="Actual R UP")
axs[0].plot(t, df["Pressure R BAM Down"], label="Actual R Down")
axs[0].set_ylabel("Pressure (kPa)")
axs[0].set_title("Right BAM Pressure: Given vs Actual")
axs[0].legend(loc="upper right")
axs[0].grid(True)

# ---------- Plot 2: Right heel strike ----------
axs[1].step(t, df["heelR"], where="post", label="Right Heel Strike")
axs[1].set_ylim(-0.2, 1.2)
axs[1].set_ylabel("HeelR")
axs[1].set_title("Right Heel Strike")
axs[1].set_yticks([0, 1])
axs[1].legend(loc="upper right")
axs[1].grid(True)

# ---------- Plot 3: Left pressures ----------
axs[2].plot(t, given_L_up, "--", label="Given L UP")
axs[2].plot(t, given_L_down, "--", label="Given L Down")
axs[2].plot(t, df["Pressure L BAM UP"], label="Actual L UP")
axs[2].plot(t, df["Pressure L BAM Down"], label="Actual L Down")
axs[2].set_ylabel("Pressure (kPa)")
axs[2].set_title("Left BAM Pressure: Given vs Actual")
axs[2].legend(loc="upper right")
axs[2].grid(True)

# ---------- Plot 4: Left heel strike ----------
axs[3].step(t, df["heelL"], where="post", label="Left Heel Strike")
axs[3].set_ylim(-0.2, 1.2)
axs[3].set_ylabel("HeelL")
axs[3].set_xlabel("Time (s)")
axs[3].set_title("Left Heel Strike")
axs[3].set_yticks([0, 1])
axs[3].legend(loc="upper right")
axs[3].grid(True)

plt.tight_layout()
plt.show()
"""