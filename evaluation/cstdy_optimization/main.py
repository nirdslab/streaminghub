import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.ndimage import gaussian_filter


np.random.seed(42)
# Sample eye tracking data (x, y) coordinates
# Replace this with your actual eye tracking data
eye_tracking_data = np.random.rand(100, 2)  # Example: 100 samples of (x, y) coordinates
np.linspace(30, 300)

# Create a 2D histogram (heatmap) of the eye tracking data
heatmap, xedges, yedges = np.histogram2d(eye_tracking_data[:, 0], eye_tracking_data[:, 1], bins=50)

# Smooth the heatmap for better visualization
heatmap = gaussian_filter(heatmap, sigma=10)

# Plot heatmap using seaborn
plt.figure(figsize=(10, 8))
sns.set_theme(style="white")  # Set background style

# Create heatmap
sns.heatmap(heatmap.T, cmap="inferno", xticklabels=False, yticklabels=False)

plt.title('Eye Tracking Heatmap')
plt.xlabel('X Coordinate')
plt.ylabel('Y Coordinate')
plt.gca().invert_yaxis()  # Invert y-axis to match eye-tracking convention (origin at top-left)
plt.show()