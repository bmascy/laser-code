import re
import os
import sys
from ConfigParser import *

class setup:
    def __init__(self, parent):
        self.cp=ConfigParser()
        try:
            self.cp.readfp(open(parent.ini_file,'r'))
	# f.close()
        except IOError:
            raise Exception,'NoFileError'

        self.gcode_string = ""
        self.move_feed_rate = self.cp.getint('Gcode', 'move_feed_rate')
        self.cut_feed_rate = self.cp.getint('Gcode', 'cut_feed_rate')
        self.power_setting = self.cp.getint('Gcode', 'power_setting')
        self.dwell_time = self.cp.getfloat('Gcode', 'dwell_time')
        self.output_file = self.cp.get('Gcode', 'output_file')
        self.use_cut_variable = self.cp.getboolean('Gcode', 'use_cut_variable')

        if self.use_cut_variable:
            self.cut_speed = '#<cutfeedrate>'
        elif len(self.cut_feed_rate) > 0:
            self.cut_speed = self.cut_feed_rate
        else:
            self.cut_speed = 10

        if self.use_cut_variable:
            self.move_speed = '#<movefeedrate>'
        elif len(self.move_feed_rate) > 0:
            self.move_speed = self.move_feed_rate
        else:
            self.move_speed = 10

    def write_gcode(self, g): 
        self.add_header()
        self.add_footer()

        f = self.output_file
        with open(f, 'w') as the_file:
            the_file.write(self.gcode_string)

    def write_polyline(self, poly):
        (x,y) = poly[0]

        self.move_no_cut(x, y)

        self.oxygen_on()
        self.cutting_tool_on()
        self.add_EOL()
        for i in poly[1:]:
            (x,y) = i
            self.move(x, y)

        self.cutting_tool_off()
        self.oxygen_off()
        self.add_EOL()

    def move(self, x, y):
        self.append('G01 X%0.4lf Y%0.4lf F%s\n' % (x, y, self.cut_speed))

    def move_no_cut(self, x, y):
        self.cutting_tool_off()
        self.append('G00 X%0.4lf Y%0.4lf F%s\n' % (x, y, self.move_speed))
        self.add_EOL()

    def add_EOL(self):
        self.append('\n')

    def cutting_tool_off(self):
        self.append('M65 P2 (LASER OFF)\n')

    def cutting_tool_on(self):
        self.append('M64 P2 (LASER ON)\nG4 P%s\n' % (self.dwell_time))

    def oxygen_on(self):
        self.append('M64 P1 (GAS LINE ON)\n')

    def oxygen_off(self):
        self.append('M65 P1 (GAS LINE OFF)\n')

    def add_footer(self):
        self.cutting_tool_off()
        self.append('M65 P0 (VENTILATION OFF)\n')
        self.append('G1 X0.000 Y0.000 %s (HOME AGAIN HOME AGAIN)\n' % self.move_speed)
        self.append('M2')
        self.add_EOL()

    def add_header(self):
        self.cut_feed_rate = self.cp.getint('Gcode', 'cut_feed_rate')

        header = ('#<movefeedrate>=%s\n'
                  '#<cutfeedrate>=%s\n'
                  'G17 G20 G40 G49 S10\n'
                  'G80 G90\n'
                  'G92 X0 Y0 (SET CURRENT POSITION TO ZERO)\n'
                  'G64 P0.005\n'
                  'M64 P0 (VENTILATION ON)\n'
                  'M65 P1 (GAS LINE OFF)\n'
                  'M65 P2 (LASER OFF)\n\n') % (self.move_feed_rate, self.cut_feed_rate)

        self.prepend(header)

    def append(self, s):
        self.gcode_string = self.gcode_string + s

    def prepend(self, s):
        self.gcode_string = s + self.gcode_string
