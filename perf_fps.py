import os
import re
from functools import reduce
from time import sleep

# 待测应用启动活动名
START_ACTIVITY = "com.wdsm.kkkwan/cn.kkk.commonsdk.WelcomeAcitivity"

# 待测应用包名
PACKAGE_NAME = 'com.wdsm.kkkwan'

# 待测应用窗口
APP_ACTIVITY = 'com.wdsm.kkkwan/org.cocos2dx.lua.AppActivity'


# 启动App
def launch_app():
    cmd = "adb shell am start -n {0}".format(START_ACTIVITY)
    os.popen(cmd)


def stop_app():
    cmd = "adb shell am force-stop {0}".format(PACKAGE_NAME)
    os.popen(cmd)


# 获取当前连接设备列表
def get_devices():
    cmd = 'adb devices'
    # os.popen(cmd) 从命令cmd打开一个管道，返回值是连接管道的文件对象，通过该对象可以进行读或写。
    content = os.popen(cmd)

    devices_info = content.readlines()

    devices = []

    for i in devices_info:
        if i.endswith('device\n'):
            devices.append(i.replace('\tdevice\n', ''))

    return devices


# 获取待测应用进程ID
def check_app_pid():

    cmd = 'adb -s {0} shell ps | findstr {1}'.format(get_devices()[0], PACKAGE_NAME)

    content = os.popen(cmd)

    pidinfo = content.readlines()

    pids = []

    for i in pidinfo:
        pids.append(i.split()[1])

    return pids


# 获取待测应用uid
def check_app_uid():

    """
    uid数据出处：/proc/{pid}/status
    :return:
    """

    cmd = "adb -s {0} shell cat /proc/{1}/status".format(get_devices()[0], check_app_pid()[0])

    content = os.popen(cmd)

    uidinfo = content.read()
    # 正则匹配Uid

    uidregex = r"Uid:\s(\d{1,6})"

    uidmatches = re.finditer(uidregex, uidinfo)

    for uidmatchNum, uidmatch in enumerate(uidmatches):
        uidmatchNum = uidmatchNum + 1

    uidnum = uidmatch.group(len(uidmatch.groups()))

    return uidnum


# 获取内存信息
def check_app_meminfo():
    """
    PSS – Proportional Set Size 实际使用的物理内存（比例分配共享库占用的内存）
    USS – Unique Set Size 进程独自占用的物理内存（不包含共享库占用的内存）
    如果没有root权限的Android手机可能获取不到uss；
    """

    # cmd = 'adb shell "dumpsys meminfo |grep {}"'.format(check_app_pid()[0])
    cmd = 'adb shell dumpsys meminfo {0}'.format(PACKAGE_NAME)

    content = os.popen(cmd)

    meminfo = content.readlines()

    total = "TOTAL"

    # 获取pss内存值
    for line in meminfo:
        if re.findall(total, line):  # 找到TOTAL 这一行
            pssnums = line.split(" ")  # 将这一行，按空格分割成一个list
            while '' in pssnums:  # 将list中的空元素删除
                pssnums.remove('')
            return pssnums[1]  # 返回总共内存使用


# 获取CPU信息
def check_app_cpuinfo():

    cmd = 'adb -s {0} shell dumpsys cpuinfo {1}'.format(get_devices()[0], PACKAGE_NAME)

    content = os.popen(cmd)

    cpuinfo = content.readlines()

    name = PACKAGE_NAME

    # 获取进程使用CPU
    for line in cpuinfo:
        if re.findall(name, line):
            cpulist = line.split(" ")
            while '' in cpulist:
                cpulist.remove('')  # 将list中的空元素删除
            return float(cpulist[0].strip('%'))  # 去掉百分号，返回一个float


# 获取流量
def check_net_flow():
    """
    rx_bytes，r代表receive，是接收数据（下行）
    tx_bytes，t代表transmit，是传输数据（上行）

    流量数据出处（举两个例子）：
    1、cat/proc/uid_stat/{uid}
    2、/proc/net/xt_qtaguid/stats

    :return:
    """

    # 获取上下行流量,需要获取两次取差值
    # 注意这里的过滤指令，如果要兼容其它系统如在Linux上跑需要调整
    cmd = 'adb -s {0} shell cat /proc/net/xt_qtaguid/stats | findstr {1}'.format(get_devices()[0], check_app_uid())

    content = os.popen(cmd)

    netinfo = content.readlines()

    rx_bytes = 0

    tx_bytes = 0

    # 获取应用流量消耗
    for line in netinfo:
        # print(line)
        netlist = line.split()
        # print(netlist)
        rx_bytes += int(netlist[5])  # 将uid多有的接收流量相加
        tx_bytes += int(netlist[7])  # 将uid多有的传输流量相加

    return rx_bytes, tx_bytes


# 获取Fps 通过SurfaceFlinger方式（Android8.0以上不支持）
def check_fps_info():

    """
    命令: adb shell dumpsys SurfaceFlinger --latency  LayerName
    这个命令能获取游戏/视频应用的fps数据
    其中LayerName在各个不同系统中获取的命令是不一样的
    在Android 6系统直接就是SurfaceView
    在Android 7系统中可以通过 dumpsys window windows | grep mSurface | grep SurfaceView 然后通过数据截取到
    在Android 8系统中可以通过 dumpsys SurfaceFlinger | grep android包名获取到

    计算方法比较简单，
    一般打印出来的数据是129行（部分机型打印两次257行，但是第一部分是无效数据，取后半部分），
    取len-2的第一列数据为end_time，取len-128的第一列数据为start_time
    fps = 127/((end_time - start_time) / 1000000.0)
    :return:
    """

    cmd = 'adb -s {0} shell dumpsys SurfaceFlinger --latency {1}'.format(get_devices()[0], APP_ACTIVITY)
    content = os.popen(cmd)
    fpsinfo = content.readlines()

    # print(fpsinfo)

    times = []

    for line in fpsinfo:
        flist = line.split()
        if len(flist) == 0:
            continue
        times.append(flist)

    start_time = int(times[-122][0])
    end_time = int(times[-2][0])

    print(start_time)
    print(end_time)

    fps = 127 / ((end_time - start_time) / 1000000000.0)
    print(fps)


# 获取Fps 通过gfxinfo方式
def GfxInfo(self):
    # 流畅度
    '''
    打开手机gfx监控: 设置-开发者选项-GPU呈现模式分析-在adb shell dumpsys gfxinfo中
    当渲染时间大于16.67，按照垂直同步机制，该帧就已经渲染超时
    那么，如果它正好是16.67的整数倍，比如66.68，则它花费了4个垂直同步脉冲，减去本身需要一个，则超时3个
    如果它不是16.67的整数倍，比如67，那么它花费的垂直同步脉冲应向上取整，即5个，减去本身需要一个，即超时4个，可直接算向下取整
    最后的计算方法思路：
    执行一次命令，总共收集到了m帧（理想情况下m=128），但是这m帧里面有些帧渲染超过了16.67毫秒，算一次jank，一旦jank，
    需要用掉额外的垂直同步脉冲。其他的就算没有超过16.67，也按一个脉冲时间来算（理想情况下，一个脉冲就可以渲染完一帧）
    所以FPS的算法可以变为：
    m / （m + 额外的垂直同步脉冲） * 60

    前提：开发者选项=>GPU呈现模式分析确保打开=>在adb shell dumpsys gfxinfo中or 在屏幕上显示为线型图
    方法仅适用于Android原生应用，不适用于游戏
    '''
    cmd = "adb -s 127.0.0.1:21503 shell dumpsys \"gfxinfo com.chuanblog91.ui|awk '/Execute/,/hierarchy/{if(i>1)print x;x=$0;i++}'\""
    content = os.popen(cmd)

    def str2float(strf):
        # 保留原本位数的小数点
        def char2num(s):
            return {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9}[s]

        def char2int(x, y):
            return 10 * x + y

        tstr = strf.split('.')
        hightre = reduce(char2int, map(char2num, tstr[0]))
        if len(tstr) > 1:
            lowre = reduce(char2int, map(char2num, tstr[1])) * (0.1 ** len(tstr[1]))
        else:
            lowre = 0
        return hightre + lowre

    gfList = []
    gfxinfo = content.readlines()
    jank_count = 0
    vsync_overtime = 0
    for gf in gfxinfo:
        if gf.strip() != '':
            gf = gf.strip().split('\t')
            render_time = str2float(gf[0]) + str2float(gf[1]) + str2float(gf[2])
            gfList.append(render_time)
            if render_time > 16.67:
                jank_count += 1
                if render_time % 16.67 == 0:
                    # 计算额外垂直脉冲次数
                    vsync_overtime += int(render_time / 16.67) - 1
                else:
                    vsync_overtime += int(render_time / 16.67)
            # print jank_count
    if len(gfList) != 0:
        gfx_count = len(gfList)
    else:
        gfx_count = 1
    fps = int(gfx_count * 60 / (gfx_count + vsync_overtime))
    # self.logDict({"GfxInfo": {"gfx_count": str(gfx_count), "jank_count": str(jank_count), "fps": str(fps)}})
    return gfx_count, jank_count, fps


if __name__ == '__main__':
    # launch_app()
    # dev = get_devices()
    # print(dev)
    # print(type(dev))
    # print(check_app_meminfo())
    # print(check_app_cpuinfo())
    # print(check_net_flow())
    # print(check_app_uid())
    # print(check_net_flow())
    print(check_fps_info())


