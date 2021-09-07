import cv2
import threading
import time
import os
import os.path as op
import datetime
import argparse
from glob import glob
from tqdm import tqdm
import curses

# 현재 웹캠이 지원하는 해상도 출력
# v4l2-ctl -d /dev/video0 --list-formats-ext


def MakeFolder(folder):
    try:
        if not op.exists(folder):
            os.makedirs(folder)
    except OSError:
        print(
            f'[Error] Failed to create directory : {folder}')


def InputChar(message=''):
    win = curses.initscr()
    win.addstr(0, 0, message)

    ch = win.getch()
    if ch in range(32, 127):
        curses.endwin()
        time.sleep(0.05)
        return chr(ch)
    else:
        time.sleep(0.05)
        return None


def MakeImageName(folder):
    now = datetime.datetime.now()
    now_datetime = now.strftime('%Y-%m-%d %H:%M:%S')
    capture_date = now.strftime('%Y%m%d')
    capture_time = now.strftime('%H%M%S')
    # capture_time = now.strftime('%H')

    image_name = '_'.join([capture_date, capture_time])
    image_name_duplicate = glob(
        f'{folder}/*{image_name}*.jpg')

    if len(image_name_duplicate) > 1:
        tmp_list = []
        for image in image_name_duplicate:
            name_split = image.split('_')
            if len(name_split) > 2:
                index = image.split('_')[-1][:-4]
                tmp_list.append(int(index))
        latest_index = max(tmp_list)

        image_name = '_'.join(
            [image_name, str(latest_index + 1)])
    elif len(image_name_duplicate) == 1:
        image_name += '_1'

    return image_name


class Timelapse(threading.Thread):

    DEFAULT_IMAGE_FOLDER = 'capture_images'
    DEFAULT_VIDEO_FOLDER = 'video_out'

    def __init__(self, width=1920, height=1080, fps=30.0, cap_num=1):
        self.cap = None
        self.width = width
        self.height = height
        self.cap_num = cap_num
        self.fps = fps
        self.vout = None
        self.run_thread = False

    def SetWidth(self, width):
        self.width = width
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)

    def SetHeight(self, height):
        self.height = height
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def SetFPS(self, fps):
        self.fps = fps
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

    def Run(self, cycle, folder=DEFAULT_IMAGE_FOLDER):
        print(f'Capture start. [image path : ./{folder}/]')
        self.cap = cv2.VideoCapture(self.cap_num)
        self.SetWidth(self.width)
        self.SetHeight(self.height)

        prev_millis = int(round(time.time() * 1000))

        try:
            while self.run_thread:
                curr_millis = int(round(time.time() * 1000))
                # ch = InputChar()

                # if ch is 'v':
                #     raise Exception('go to make video')
                if (curr_millis - prev_millis) % cycle == 0:
                    ret, frame = self.cap.read()
                    if ret:
                        MakeFolder(folder)
                        image_name = MakeImageName(folder)
                        now_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                        cv2.imwrite(f'{folder}/{image_name}.jpg', frame)
                        print(
                            f'[{now_datetime}] Capture success! [press "v" to make video]\r')
                    else:
                        print('Camera capture failed!')
                        self.Destroy()
                        break
        except KeyboardInterrupt:
            self.Stop()
            key = input('\nMake video? [y/n]')
            while True:
                if key.lower() == "y":
                    self.MakeVideo(src_path=folder,
                                   des_path=Timelapse.DEFAULT_VIDEO_FOLDER)
                break
        # except Exception as e:
        #     self.MakeVideo(src_path=folder,
        #                    des_path=Timelapse.DEFAULT_VIDEO_FOLDER)

    def MakeVideo(self, src_path=DEFAULT_IMAGE_FOLDER, des_path=DEFAULT_VIDEO_FOLDER):
        print('Make video start. [video path : {des_path}]')
        image_list = glob(f'{src_path}/*.jpg')
        image_list.sort()
        size = (self.width, self.height)

        MakeFolder(des_path)

        self.vout = cv2.VideoWriter(
            f'{des_path}/out.mp4', cv2.VideoWriter_fourcc(*'H264'), self.fps, size)

        for image in tqdm(image_list, desc='image read'):
            frame = cv2.imread(image)
            self.vout.write(frame)
        self.vout.release()

    def Start(self, cycle):
        self.run_thread = True
        self.Run(cycle)

    def Stop(self):
        self.run_thread = False

    def Destroy(self):
        self.cap.release()


def main(args):
    size, cycle, capnum, only_make_video = args.size, args.cycle, args.capnum, args.only_make_video
    if only_make_video:
        timelapse = Timelapse().MakeVideo(src_path='capture_images', des_path='video')
    else:
        timelapse = Timelapse(
            width=size[0], height=size[1], fps=30.0, cap_num=capnum)
        timelapse.Start(cycle)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('--only_make_video', '-omv',
                        help='make video', action="store_true")
    parser.add_argument('--size', '-s', nargs="+", type=int,
                        help='capture width')
    parser.add_argument('--cycle', '-t', type=int,
                        help='capture cycle')
    parser.add_argument('--capnum', '-c', type=int,
                        help='video number')

    args = parser.parse_args()

    main(args)
