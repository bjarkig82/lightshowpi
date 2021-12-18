from rpi_lcd import LCD as RPI_LCD
import math
import threading
import time
import unicodedata
import queue



class LCD(RPI_LCD):
  def __init__(self, address=0x27, bus=1, width=20, rows=4):
    self.playing = False
    self.text_queue = queue.Queue()
    threading.Thread(target=self.text_queue_worker, daemon=True).start()

    if not address is None:
      super(LCD, self).__init__(address, bus, width, rows)
    else:
      self.address = None
  
  def text_queue_worker(self):
    while True:
      item = self.text_queue.get()
      super().text(item[0], item[1], item[2])
      self.text_queue.task_done()

  def write(self, byte, mode=0):
    if not self.address is None:
      super().write(byte, mode)

  def scroll_text(self, text, line, align='left'):
    scrolling_text = text + ' ' * round(self.width/2) + text
    text_length = len(text)
    first_letter = 0
    
    while self.playing:
      last_letter = first_letter + self.width
      self.text_queue.put([scrolling_text[first_letter:last_letter], line, align])
      time.sleep(0.5)
      first_letter = (first_letter + 1) % (text_length + round(self.width/2))

  def strip_accents(self, text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if unicodedata.category(c) != 'Mn')

  def text(self, text, line, align='left'):
    if not self.address is None:
      self.playing = True
      normalized_text = self.strip_accents(text)

      if len(normalized_text) > self.width:
        scroll_text = threading.Thread(target=self.scroll_text, name='Scroll Text', args=[normalized_text, line, align], daemon=True)
        scroll_text.start();
      else:
        self.text_queue.put([text, line, align])

  def get_time_string(self, time):
    minutes = math.floor(time / 60)
    seconds = time % 60
    return f'{str(minutes).zfill(2)}:{str(seconds).zfill(2)}'

  def timer(self, max_time, line, align):
    current_time = 0
    max_time_string = self.get_time_string(max_time)
    self.playing = True

    while current_time < max_time and self.playing:
      current_time_string = self.get_time_string(current_time)
      timer_string = current_time_string + ' / ' + max_time_string

      self.text_queue.put([timer_string, line, align])
      time.sleep(1)
      current_time +=1

  def display_timer(self, max_time, line, align='left'):
    if not self.address is None:
        timer = threading.Thread(target=self.timer, name='Timer', args=[max_time, line, align], daemon=True)
        timer.start();

  def get_text_line(self, text):
    if not self.address is None:
      return super().get_text_line(text)
    return ''

  def clear(self):
    self.playing = False
    if self.address:
      super().clear()