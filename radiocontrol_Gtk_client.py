#import pygtk
#pygtk.require("2.0")
#import gtk
#import gtk.glade
from gi.repository import Gtk, Gdk, GLib, GObject, Pango
#import pango
import string
import time
import math
import socket
import sys
import threading
import serial
import numpy as np

# Definitions:

USB = 1
LSB = 2
CW = 3
CWN = 4
AM = 5

I2C_ERR = 1
SOCK_ERR = 2
COMM_LOST = 3
UART_ERR = 4

RX = 1
TX = 2
MUTE = 3

# Communication settings:

comm_mode = "Serial"  # Serial or Socket
serial_port1 = "/dev/ttyUSB0"
serial_port2 = "/dev/ttyS0"
serial_port3 = "/dev/ttyAMA0"
socket_addr = "192.168.0.25"
socket_port = 8899

# Radio parameters:

if_freq = 45000

# Initialization values:

freq = 1000.0
vol = 22
volscroll = 0
clar = 0
clarscroll = 0
sq = 0
sqscroll = 0
quit_flag = 0
comm_fail = 0
mode_set = USB
comm_lock = 0

# Connection routine:

if comm_mode == "Socket":
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except (socket.error, msg):
        print ("Failed to create socket. Error code: " + str(msg[0]) + " , Error message : " + msg[1])
        sys.exit()
   
    try:
        sock.connect((socket_addr , socket_port))
    except socket.error:
        print ("Connection failed.")
        sys.exit()
    
    print ("Socket connected.")

elif comm_mode == "Serial":
    try:
        ser = serial.Serial(serial_port1,timeout=1)
    except:
        try:
            ser = serial.Serial(serial_port2,timeout=1)
        except:
            try:
                ser = serial.Serial(serial_port3,timeout=1)
            except:
                print ("No serial connection available. Aborting.")
                sys.exit()

# Function definitions:

def setConf(mode):
    global mode_set
    global comm_lock

    if (quit_flag==1):
        return

    if (mode == AM):
        message = "mode AM "
        cmd = b'\x40'
    elif (mode == LSB):
        message = "mode LSB "
        cmd = b'\x70' # LSB
    elif (mode == USB):
        message = "mode USB "
        cmd = b'\x78' # USB
    elif (mode == CW):
        message = "mode CW  "
        cmd = b'\x70' # LSB
    elif (mode == CWN):
        message = "mode CWN "
        cmd = b'\x60' # LSB narrow
    mode_set = mode
    starttime = time.time()
    while (comm_lock != 0):
        time.sleep(0.01)
        if (time.time()-starttime > 3):
            print("Timeout in setConf.")
            return
    comm_lock = 1
    if comm_mode == "Socket":
        try:
            sock.sendall(message.encode())
        except socket.error:
            print ("Send failed")
            comm_fail = SOCK_ERR
    elif comm_mode == "Serial":
        try:
            ser.write(cmd + b'\x00\xa0\x00\x00')
        except:
            print ("Send failed")
            comm_fail = COMM_LOST
    comm_lock = 0

def updateFreq():
    global freq
    global comm_lock
    global mode_set

    if (quit_flag==1):
        return

    if (freq<0):
        freq = 0
    elif (freq>30000):
        freq=30000
    message = "freq " + str(freq) + " "
    entryone.set_text("{:^16}".format("{:,.3f} kHz".format(freq))) # Add clar value!
    tune_freq = freq # if_freq-freq
    if (mode_set == USB):
        tune_freq = tune_freq - 1.8
    elif (mode_set == LSB):
        tune_freq = tune_freq + 1.8
    elif (mode_set == CW):
        tune_freq = tune_freq + 0.9
    elif (mode_set == CWN):
        tune_freq = tune_freq + 0

    starttime = time.time()
    while (comm_lock != 0):
        time.sleep(0.01)
        if (time.time()-starttime > 3):
            print("Timeout in updateFreq.")
            return
    comm_lock = 1    
    #print("Freq lock")

    if comm_mode == "Socket":
        try:
            sock.sendall(message.encode())
            Gtk.Entry.set_icon_from_icon_name(entryone,Gtk.EntryIconPosition.SECONDARY,"gtk-ok")
        except socket.error:
            comm_fail = SOCK_ERR
    elif comm_mode == "Serial":
        ftw = tune_freq*279.620266666666 #pow(2,25)/(6*20000)
        ftw_toptop = math.floor(ftw/16777216); 
        ftw_topbot = math.floor((ftw-ftw_toptop*16777216)/65536) #math.floor(ftw/pow(2,16))
        ftw_bottop = math.floor((ftw-ftw_toptop*16777216-ftw_topbot*65536)/256) #math.floor((ftw-ftw_top*pow(2,16))/pow(2,8))
        ftw_botbot = round(ftw%256) #round(ftw%pow(2,8))
        try:
            ser.write(bytes([0xc0,np.uint8((np.int8(clar) << 1) | np.uint8(ftw_toptop)), np.uint8(ftw_topbot), np.uint8(ftw_bottop), np.uint8(ftw_botbot)]))
            #ser.write(bytes([0xc0,np.uint8(ftw_toptop), np.uint8(ftw_topbot), np.uint8(ftw_bottop), np.uint8(ftw_botbot)]))
            Gtk.Entry.set_icon_from_icon_name(entryone,Gtk.EntryIconPosition.SECONDARY,"gtk-ok")
        except:
            print("Freq fail")
            comm_fail = COMM_LOST
    comm_lock = 0
    #print("Freq unlock")

def updateVol():
    global vol
    global comm_fail
    global comm_lock

    if (quit_flag==1):
        return

    starttime = time.time()
    while (comm_lock != 0):
        time.sleep(0.01)
        if (time.time()-starttime > 3):
            print("Timeout in updateVol.")
            return
    comm_lock = 1
    #print("Vol lock")
    if comm_mode == "Socket":
        message = "vol " + str(int(vol)) + " "
        try:
            sock.sendall(message.encode())
        except:
            comm_fail = 1
    elif comm_mode == "Serial":
        try:
            ser.write(bytes([0,0,0,0,0]))
            ser.write(bytes([0,0,0,0,0]))
            ser.write(bytes([0,0,0,0,0]))
            ser.write(bytes([128,0,0,int(sq),31-int(vol)]))
        except:
            comm_fail = COMM_LOST
    comm_lock = 0
    #print("Vol unlock")

def updateRssi():  # To be run as thread
    global quit_flag
    global comm_fail
    global comm_lock
    while (quit_flag == 0):
        #print("rssi")
        time.sleep(0.2)
        starttime = time.time()
        while (comm_lock != 0):
            time.sleep(0.01)
            if (time.time()-starttime > 3):
                print("Timeout in updateRssi.")
                return
        comm_lock = 1
        #print("RSSI lock")
        if comm_mode == "Serial":
            #try:
            if ser.inWaiting() > 0:
                ser.flushInput()
            ser.write(b'\x00\x00\x00\x00\x00')
            statusbyte=ser.read()
            if (statusbyte):
                rssi_val = (statusbyte[0] & b'\x3f'[0]) - 4
                #print(rssi_val)
                GLib.idle_add(updateRssiGtk, rssi_val)
                if (statusbyte[0] & b'\x80'[0]) > 0:
                    GLib.idle_add(update_RX_TX_Indicator, TX)
                else:
                    if (statusbyte[0] & b'\x40'[0]) > 0:
                        GLib.idle_add(update_RX_TX_Indicator, RX)
                    else:
                        GLib.idle_add(update_RX_TX_Indicator, MUTE)
                ser.flushInput()
                comm_fail = 0
            else:
                comm_fail = COMM_LOST
        comm_lock = 0
        #print("RSSI unlock")

def commMonitor(): # To be run as thread
    global quit_flag
    global comm_fail
    while (quit_flag == 0):
        time.sleep(1)
        GLib.idle_add(commMonitorGtk, comm_fail)

def commMonitorGtk(comm_fail):
    if (comm_fail == SOCK_ERR):
        Gtk.Label.set_text(statustext, "Error. No socket connection.")
    elif (comm_fail == I2C_ERR):
        Gtk.Label.set_text(statustext, "Error. No I2C connection.")
    elif (comm_fail == UART_ERR):
        Gtk.Label.set_text(statustext, "Error. No serial connection.")
    elif (comm_fail == COMM_LOST):
        Gtk.Label.set_text(statustext, "Error. No connection.")
    else:
        Gtk.Label.set_text(statustext, "Connection established.")

def updateRssiGtk(rssi_val):
    Gtk.LevelBar.set_value (rssibar, rssi_val)

def update_RX_TX_Indicator(mode):
    if (mode == RX):
        Gtk.Label.set_text(txrxlabel, "RX")
    elif (mode == TX):
        Gtk.Label.set_text(txrxlabel, "TX")
    elif (mode == MUTE):
        Gtk.Label.set_text(txrxlabel, "RX MUTE")
    else:
        Gtk.Label.set_text(txrxlabel, "")

# Gtk signals handler:

class Handler:
    def OnDeleteWindow(self, *args):
        Gtk.main_quit(*args)

    def OnBandUpPressed(self, *args):
        global freq
        freq = freq + 1000
        updateFreq()

    def OnBandDownPressed(self, *args):
        global freq
        freq = freq - 1000
        updateFreq()

    def FreqScroll(self, scroller, event):
        global freq
        global mode_set
        if event.direction == Gdk.ScrollDirection.UP:
            if (mode_set==AM):
                freq = freq + 2
            elif (mode_set==USB or mode_set==LSB or mode_set==CW):
                freq = freq + 0.1
            elif (mode_set==CWN):
                freq = freq + 0.05
        elif event.direction == Gdk.ScrollDirection.DOWN:
            if (mode_set==AM):
                freq = freq - 2
            elif (mode_set==USB or mode_set==LSB or mode_set==CW):
                freq = freq - 0.1
            elif (mode_set==CWN):
                freq = freq - 0.05
        updateFreq()   

    def VolScroll(self, scroller, event):
        global volscroll
        #Gtk.Label.set_text(labelone, "Scroll!")
        if event.direction == Gdk.ScrollDirection.UP:
            volscroll = 1
        elif event.direction == Gdk.ScrollDirection.DOWN:
            volscroll = 2

    def VolChange(self, r):
        global vol
        global volscroll
        time.sleep(0.01)
        vol = r.get_value()
        if (volscroll == 1): # scrolled up
            r.set_value(3)
            vol = r.get_value()
        elif (volscroll == 2): # scrolled down
            r.set_value(3)
            vol = r.get_value()
        volscroll = 0
        updateVol()

    def ClarScroll(self, scroller, event):
        global clarscroll
        #Gtk.Label.set_text(labelone, "Scroll!")
        if event.direction == Gdk.ScrollDirection.UP:
            clarscroll = 1
        elif event.direction == Gdk.ScrollDirection.DOWN:
            clarscroll = 2

    def ClarChange(self, r):
        global clar
        global clarscroll
        time.sleep(0.01)
        clar = r.get_value()
        if (clarscroll == 1): # scrolled up
            r.set_value(3)
            clar = r.get_value()
        elif (clarscroll == 2): # scrolled down
            r.set_value(3)
            clar = r.get_value()
        clarscroll = 0
        updateFreq()

    def SqScroll(self, scroller, event):
        global sqscroll
        if event.direction == Gdk.ScrollDirection.UP:
            sqscroll = 1
        elif event.direction == Gdk.ScrollDirection.DOWN:
            sqscroll = 2

    def SqChange(self, r):
        global sq
        global sqscroll
        time.sleep(0.01)
        sq = r.get_value()
        if (sqscroll == 1): # scrolled up
            r.set_value(3)
            sq = r.get_value()
        elif (sqscroll == 2): # scrolled down
            r.set_value(3)
            sq = r.get_value()
        sqscroll = 0
        updateVol()   # Sq in the same adress as volume

    def NewFreqEntry(self,e,*args):
        global freq
        freqstring = e.get_text()
        freqstring = freqstring.rstrip(string.ascii_letters+" ,") # remove letters at beg and end
        freqstring = "".join(freqstring.split()) # Remove spaces
        freqstring = "".join(freqstring.split(',')) # Remove commas
        freq = float(freqstring)
        updateFreq()

    def FreqEdited(self,e,*args):
        Gtk.Entry.set_icon_from_icon_name(e,Gtk.EntryIconPosition.SECONDARY,"gtk-execute")

    def ModeToggle(self,b):
        
        if (b == USB_button and Gtk.ToggleButton.get_active(USB_button)):
            setConf(USB)
        elif (b == LSB_button and Gtk.ToggleButton.get_active(LSB_button)):
            setConf(LSB)
        elif (b == CW_button and Gtk.ToggleButton.get_active(CW_button)):
            setConf(CW)
        elif (b == CWN_button and Gtk.ToggleButton.get_active(CWN_button)):
            setConf(CWN)
        elif (b == AM_button and Gtk.ToggleButton.get_active(AM_button)):
            setConf(AM)
        updateFreq()

# Set up GUI and connect signals to handler:

builder = Gtk.Builder()
builder.add_from_file("radiocontrol.glade")
builder.connect_signals(Handler())

volscale = builder.get_object("scale1")
volscale.add_events(Gdk.EventMask.SCROLL_MASK)

clarscale = builder.get_object("scale2")
clarscale.add_events(Gdk.EventMask.SCROLL_MASK)

sqscale = builder.get_object("scale3")
sqscale.add_events(Gdk.EventMask.SCROLL_MASK)

labelone = builder.get_object("label2")
#Gtk.Label.set_text(labelone, "Ugh")
statustext = builder.get_object("statuslabel")
txrxlabel = builder.get_object("label7")

entryone = builder.get_object("entry1")
entryone.add_events(Gdk.EventMask.SCROLL_MASK)

#nyfont = pango.FontDescription("Sans 18")
#Gtk.Widget.modify_font(entryone, nyfont)

rssibar = builder.get_object("rssibar")
Gtk.LevelBar.set_value (rssibar, 0)

USB_button = builder.get_object("USB_button")
LSB_button = builder.get_object("LSB_button")
CW_button = builder.get_object("CW_button")
CWN_button = builder.get_object("CWN_button")
AM_button = builder.get_object("AM_button")


#entryone_context = entryone.get_style_context ()
#entryone_context.add_provider(css_provider,1)
#entryone.add_events(Gdk.EventMask.SCROLL_MASK) 

window = builder.get_object("window1")

#window_context = window.get_style_context ()
#window_context.add_provider(css_provider,1)

css ="""
#entry1 {font: Sans 18; color: rgb(10,128,0);}
GtkWindow {background-color: rgb(200, 220, 220);}
""".encode()

css_provider = Gtk.CssProvider()
css_provider.load_from_data (css)

Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(), 
    css_provider,     
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)


#color_bg = Gdk.Color(0xffff,0xffff,0xeeee)
#color_fg = Gdk.Color(0x1111,0x1111,0x1111)
#color_text = Gdk.Color(0x0000,0x0000,0x0000)

#Gtk.Widget.modify_bg(window, Gtk.StateFlags.NORMAL, color_bg);
#Gtk.Widget.modify_fg(window, Gtk.StateFlags.NORMAL, color_fg);
#Gtk.Widget.modify_text(window, Gtk.StateFlags.NORMAL, color_text);

window.show_all()  

# Initialize radio parameters:

setConf(LSB)
updateFreq()
updateVol()

# Create and start threads:

GObject.threads_init()

threadRssi = threading.Thread(target=updateRssi)
threadCommMon = threading.Thread(target=commMonitor)

threadRssi.daemon = True
threadRssi.start()
threadCommMon.daemon = True
threadCommMon.start()

# Start main loop:

Gtk.main()

# When exiting tell threads to abort:

quit_flag = 1

# Close connection:

if comm_mode == "Socket":
    sock.close()
elif comm_mode == "Serial":
    ser.close()

# End
