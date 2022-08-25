import time
import csv
import numpy as np
from watchdog.events import FileSystemEventHandler

import global_var

# 状态维度和动作集
STATE_DIM = 16
ACTION_LIST = {
    0: 'DoTacHeadEvade',
    1: 'DoTacPointAtk',
    2: 'DoTacToTar',
    3: 'DoTacAltClimbP30',
    4: 'DoTacAltClimbP60',
    5: 'DoTacNoseDiveM30',
    6: 'DoTacNoseDiveM600',
    7: 'DoTacStaHov',
    8: 'DoTurnLeft30',
    9: 'DoTurnLeft60',
    10: 'DoTurnRight30',
    11: 'DoTacHeadEvade',
    12: 'DoTurnEvad30',
    13: 'DoTurnEvad60',
    14: 'DoTacWpnShoot',
    15: 'SwitchGuideFlight'
}

# 文件路径
STATE_FILE = r'../ACAIStrategyDemo/dist/state1.csv'
ACTION_FILE = r'../ACAIStrategyDemo/dist/action1.csv'
REWARD_FILE = r'../ACAIStrategyDemo/dist/reward1.csv'
WATCH_PATH = r'../ACAIStrategyDemo/dist'  # 监控目录


# 监控state变化
def monitor_state():
    with open(STATE_FILE, "r") as f:
        reader = csv.reader(f)
        data = list(reader)
        state = data[-1]
    state = np.array(list(map(float, state)), dtype=np.float32)
    global_var.set_value('state', state)
    global_var.set_value('state_signal', True)


# 监控reward变化
def monitor_reward():
    with open(REWARD_FILE, "r") as f:
        reader = csv.reader(f)
        data = list(reader)
        reward = data[-1]
    reward = int(reward)
    global_var.set_value('reward', reward)
    global_var.set_value('reward_signal', True)


# action输出转换
def action_transfer(action):
    if action >= 14:
        return '\n1,' + str(action - 13)
    else:
        return '\n0,' + str(action)


# watchdog文件监控器重写
class FileMonitorHandler(FileSystemEventHandler):
    def __init__(self, **kwargs):
        super(FileMonitorHandler, self).__init__(**kwargs)
        self._watch_path = WATCH_PATH

    def on_modified(self, event):
        if not event.is_directory:
            file_path = event.src_path
            if file_path[-13:] == 'state_run.csv':
                print("state更新: %s " % file_path)
                monitor_state()
            if file_path[-14:] == 'reward_run.csv':
                print("reward更新: %s " % file_path)
                monitor_reward()

    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            if file_path[-3:] == 'end':
                print('比赛终止')
                global_var.set_value('done', True)
                global_var.set_value('race_state', 'end')
            if file_path[-5:] == 'fight':
                print('作战状态')
                global_var.set_value('race_state', 'fight')
            if file_path[-8:] == 'outfight':
                print('脱战状态')
                global_var.set_value('race_state', 'outfight')


class StateSpace(object):
    # 状态类
    shape = 0
    state = np.empty(shape=shape)

    def __init__(self, dim):
        self.shape = dim
        self.state = np.empty(shape=self.shape)


class ActionSpace(object):
    # 动作类
    action_list = {}
    n = 0

    def __init__(self, action_list):
        self.action_list = action_list
        self.n = len(self.action_list)


class Env(object):
    # 环境类
    observation_space = None
    action_space = None
    state = None

    def __init__(self):
        self.action_space = ActionSpace(ACTION_LIST)
        self.observation_space = StateSpace(STATE_DIM)
        self.state = self.observation_space.state

    # 环境更新
    def step(self, action):
        with open(ACTION_FILE, "a") as f:
            f.write(action_transfer(action))
        print('采取行动为：' + ACTION_LIST[action])

        while not global_var.get_value('state_signal'):
            time.sleep(0.001)
        self.state = global_var.get_value('state')
        global_var.set_value('state_signal', False)

        while not global_var.get_value('reward_signal'):
            time.sleep(0.001)
        reward = global_var.get_value('reward')
        global_var.set_value('reward_state', False)

        done = global_var.get_value('done')

        return self.state, reward, done, {}

    # 环境重置
    def reset(self):
        while global_var.get_value('race_state') != 'fight':
            time.sleep(0.01)
        with open(STATE_FILE, "r") as f:
            reader = csv.reader(f)
            data = list(reader)
            state = data[1]
        self.state = np.array(list(map(float, state[1:])), dtype=np.float32)
        return self.state
