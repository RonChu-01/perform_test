from matplotlib import pyplot as plt
from matplotlib import animation
from perf_fps import *

fig = plt.figure()
ax1 = fig.add_subplot(2, 1, 1, xlim=(0, 100), ylim=(0, 800))
ax2 = fig.add_subplot(2, 1, 2, xlim=(0, 100), ylim=(0, 100))
line, = ax1.plot([], [], lw=2)
line2, = ax2.plot([], [], lw=2)
x = []
y = []
y2 = []


def init():
    line.set_data([], [])
    # line2.set_data([], [])
    return line, line2


def getx():
    t = "0"
    return t


def animate(i):
    x.append(int(getx()) + i)
    y.append(int(check_app_meminfo())/1024)  # 每执行一次去获取一次值加入绘制的data中
    y2.append(check_app_cpuinfo())
    print(x, y)
    line.set_data(x, y)
    line2.set_data(x, y2)
    return line, line2


if __name__ == '__main__':
    anim1 = animation.FuncAnimation(fig, animate, init_func=init,  frames=1000, interval=30)
    plt.show()
