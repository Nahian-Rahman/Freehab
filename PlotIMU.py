import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# File names
# ==============================
files = {
    "Ajmal - No Load": "AjmalNOLoad.csv",
    "Ajmal - Load": "AjmolWithLoad.csv",
    "Tianyu - No Load": "TianyuNoLoad.csv",
    "Tianyu - Load": "TianyuWithLoad.csv",
}

# ==============================
# Column names
# Change these if your CSV uses different names
# ==============================
time_col = "Time"
right_knee_col = "R knee"
left_knee_col = "L knee"

# ==============================
# Create figure
# ==============================
fig, axes = plt.subplots(2, 2, figsize=(14, 8), sharex=False, sharey=True)
axes = axes.flatten()

for ax, (title, filename) in zip(axes, files.items()):

    df = pd.read_csv(filename)
    df.columns = df.columns.str.strip()

    ax.plot(df[time_col], df[right_knee_col], label="Right knee")
    ax.plot(df[time_col], df[left_knee_col], label="Left knee")

    ax.set_title(title)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Knee angle (deg)")
    ax.grid(True)
    ax.legend()

plt.tight_layout()
plt.savefig("knee_angle_four_trials.png", dpi=300)
plt.show()