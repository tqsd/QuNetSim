import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as patches
import numpy as np


def draw(BUFFER_STATUS, DATA_FRAME_LENGTH, E_BUFFER_RECEIVER, E_BUFFER_SENDER, RECEIVED_BITS, RECEIVED_FRAMES,
         TRANSM_TYPE, TRANSMITTED_BITS, TRANSMITTED_FRAMES):
    buffer_status = BUFFER_STATUS
    if buffer_status > DATA_FRAME_LENGTH:
        buffer_status = DATA_FRAME_LENGTH
    ys = [E_BUFFER_RECEIVER, RECEIVED_BITS, 0, TRANSMITTED_BITS, E_BUFFER_SENDER, buffer_status]
    plt.cla()
    xs = ["EPR pair buffer\nreceiver", "received\nframes", "channel\nactivity", "transmitted\nframes",
          "EPR pair buffer\nsender", "incoming message\nbuffer"]
    plt.style.use('ggplot')
    x_pos = [0, 1, 2, 3, 4, 5]
    color = "black"
    word_color = "white"
    word = "data transmission"
    if TRANSM_TYPE == "DENSE":
        color = "green"
        word_color = "black"
    if TRANSM_TYPE == "EPR":
        color = "yellow"
        word_color = "black"
        word = "EPR pair transmission"
    if TRANSM_TYPE == "NONE":
        color = "white"
        word_color = "black"
        word = "idle"
    rect = patches.Rectangle((1.5, 3), 1, 2, edgecolor=color, facecolor=color, fill=True)
    plt.bar(x_pos, ys, color=["green", "yellow", color, "orange", "green", "red"])
    plt.xticks(x_pos, xs)
    plt.yticks([16, 32], ["16", "32"])
    ax = plt.gca()
    ax.grid(False)
    ax.add_patch(rect)
    rx, ry = rect.get_xy()
    cx = rx + rect.get_width() / 2.0
    cy = ry + rect.get_height() / 2.0
    ax.annotate(word, (cx, cy), color=word_color, weight='bold', fontsize=6, ha='center', va='center')
    ax.text(0.9, 1, RECEIVED_FRAMES, fontsize=15)
    ax.text(2.9, 1, TRANSMITTED_FRAMES, fontsize=15)
    ax.text(4.9, 1, int(np.ceil(BUFFER_STATUS / DATA_FRAME_LENGTH)), fontsize=15)
