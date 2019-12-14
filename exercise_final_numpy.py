import nn
import copy
import numba
import Modules
import warnings
import numpy as np
import matplotlib.pyplot as plt
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms


warnings.filterwarnings('ignore')

### 建议把更多的激活函数模块也写上去。然后多做测试。卷积尝试加速
### 跟pytorch版本进行比对
# 今天至少把线性的全部写出来，最后优化卷积的实现
# 卷积核是4维，还是要写4维，因为输入通道就1，但是输出通道可以尝试一下调参数

# Global variables
N_CLASS = 10
BATCH_SIZE = 64
TRAIN_EPOCHS = 25
LEARNING_RATE = 0.001
LOG_ITERATIONS = 100


train_set = datasets.MNIST('./data',
                           train=True,
                           transform=transforms.ToTensor(),
                           download=True)

test_set = datasets.MNIST('./data',
                          train=True,
                          transform=transforms.ToTensor(),
                          download=True)

# Data Loader
train_loader = DataLoader(dataset=train_set,
                          batch_size=BATCH_SIZE,
                          shuffle=True)

test_loader = DataLoader(dataset=test_set,
                         batch_size=BATCH_SIZE,
                         shuffle=False)

model = Modules.MLP()

# 画出实验的学习曲线【把这两个函数的api看看他们各自的功能，记住要对结果进行画图。测试集准确率，训练集准确率画一张图，loss的训练过程画一张图】
def plot_learning_curves(experiment_data):
    # 生成图像.
    fig, axes = plt.subplots(3, 4, figsize=(22, 12))
    st = fig.subtitle(
        "Learning Curves for all Tasks and Hyper-parameter settings",
        fontsize="x-large"
    )
    # 画出所有的学习曲线. i表示不同模型，j表示不同setting
    for i, results in enumerate(experiment_data):
        for j, (setting, train_accuracy, test_accuracy) in enumerate(results):
            # Plot.
            xs = [x * LOG_ITERATIONS for x in range(1, len(train_accuracy)+1)]
            axes[j, i].plot(xs, train_accuracy, label='train_accuracy')
            axes[j, i].plot(xs, test_accuracy, label='test_accuracy')
            # Prettify individual plots
            axes[j, i].ticklabel_format(style='sci', axis='x', scilimits=(0, 0))
            axes[j, i].set_xlabel('Number of samples processed')
            axes[j, i].set_ylabel('Epochs: {}, Learning rate: {}. Accuracy'.format(*setting))
            axes[j, i].set_title('Task {}'.format(i+1))
            axes[j, i].legend()
        # Prettify overall figure.
        plt.tight_layout()
        st.set_y(0.95)
        fig.subplots_adjust(top=0.91)
        plt.show()

# 生成结果的摘要表
def plot_summary_table(experiment_data):
    # 填充数据
    cell_text = []
    rows = []
    columns = ['Setting 1', 'Setting 2', 'Setting 3']
    for i, results in enumerate(experiment_data):
        rows.append('Model {}'.format(i + 1))
        cell_text.append([])
        for j, (setting, train_accuracy, test_accuracy) in enumerate(results):
            cell_text[i].append(test_accuracy[-1])
    # 生成表
    fig = plt.figure(frameon=False)
    ax = plt.gca()
    the_table = ax.table(
        cellText = cell_text,
        rowLabels = rows,
        colLabels = columns,
        loc = 'center'
    )
    the_table.scale(1, 4)
    # Prettify.
    ax.patch.set_facecolor('None')
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)



def train(epoch):
    sum_loss = 0.0  # 用来每LOG_ITERATIONS打印一次平均loss
    for batch_idx, (inputs, labels) in enumerate(train_loader):
        # forward + backward + step
        inputs, labels = inputs.numpy(), labels.numpy()
        labels = one_hot(labels, N_CLASS)   # one-hot
        loss = model.train(inputs, labels, LEARNING_RATE)
        sum_loss += loss
        if batch_idx != 0 and batch_idx % LOG_ITERATIONS == 0:
            print('epoch: %d, batch_idx: %d average_batch_loss: %f'
                  % (epoch + 1, batch_idx, sum_loss / LOG_ITERATIONS))
            sum_loss =0.0


def test(epoch):
    correct = 0
    total = 0
    for (inputs, labels) in test_loader:
        inputs, labels = inputs.numpy(), labels.numpy()
        outputs = model.eval(inputs)
        # 取得分最高的那个类
        predicted = np.argmax(outputs, 1)
        total += labels.shape[0]
        correct += (predicted == labels).sum()
    if epoch == 0:
        print('模型初始化后训练前的测试集识别准确率为：%f%%' % (100 * correct / total))
    else:
        print('第%d个epoch的测试集识别准确率为：%f%%' % (epoch + 1, (100 * correct / total)))

def one_hot(labels, n_class):
    return np.array([[1 if i == l else 0 for i in range(n_class)] for l in labels])

# 训练前先测试一下模型
test(0)
for epoch in range(TRAIN_EPOCHS):
    train(epoch)
    test(epoch)
    # torch.save(model.state_dict(), '%s/net_%03d.pth' % (opt.outf, epoch + 1))


