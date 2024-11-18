import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# Create figure and axes
fig, ax = plt.subplots()
line, = ax.plot([], [])

# Set plot limits
ax.set_xlim(0, 10)
ax.set_ylim(0, 1)

# Initialize data
xdata, ydata = [], []

def animate(i):
    # Generate new data point
    x = i / 10
    y = np.random.rand()

    # Append data to lists
    xdata.append(x)
    ydata.append(y)

    # Update line data
    line.set_data(xdata, ydata)

    return line,

# Create animation
fig, ax = plt.subplots()
line, = ax.plot([], [])
ani = animation.FuncAnimation(fig, animate, interval=1000)

plt.show()