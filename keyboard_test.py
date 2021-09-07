import curses
import time


def input_char(message, timeout=0, condition=None):
    try:
        win = curses.initscr()
        win.addstr(0, 0, message)
        while True:
            ch = win.getch()
            if ch in range(32, 127):
                break
            time.sleep(0.05)
    finally:
        curses.endwin()
    return chr(ch)


c = input_char('Do you want to continue? y/[n]')
print(c)
if c.lower() in ['y', 'yes']:
    print('yes')
else:
    print('no (got {})'.format(c))
