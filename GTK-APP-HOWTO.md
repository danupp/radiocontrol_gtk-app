## How to set up the FPGA board and simple RF board for control over a Gtk applet running on Raspberry Pi or other Linux system

First solder JP1 on the FPGA board to select serial / UART communication. Make a cable with crossed signal headers and connect GND-GND, RxD-TxD and TxD-RxD between the FPGA board (K7) and the P1 header of your Raspberry Pi. (Check schematics for pin placements.)

On the Raspberry Pi the serial port might be turned off and/or occupied by the system. To fix this, edit the file at /boot/config.txt:
```
sudo nano /boot/config.txt
```
And make sure that there is a line saying:
```
enable_uart=1
```
Then, run:
```
sudo raspi-config
```
and select "Advanced Options" -> "Serial" -> "No" and reboot.

Then you need to install Python 3 and necessary modules by issuing:
```
sudo apt-get update
sudo apt-get install python3 python3-gi gir1.2-gtk-3.0 gir1.2-gtk-2.0 python-glade2 python3-serial python3-numpy
```
These are the packages that seem necessary on a Raspberry Pi with Raspbian Jessie 2016-05-27. Depending on your configuration many of these may already be installed.
On Raspberry Pi, it might also be a good idea to update to the latest system packages. This takes usually a while though! Issue:
```
sudo apt-get dist-upgrade
```

In order to get the application files you can either download manually from the gtk directory at GitHub (https://github.com/ast/dspsdr) or use wget in a terminal to get them without using a browser:
```
mkdir radiocontrol
cd radiocontrol/
wget https://raw.githubusercontent.com/ast/dspsdr/master/gtk/radiocontrol_Gtk_client.py
wget https://raw.githubusercontent.com/ast/dspsdr/master/gtk/radiocontrol.glade
```
Now, if you have an X session running (issue `startx`), you should be able to run the applet with:
```
python3 radiocontrol_Gtk_client.py
```
The program steps through the following potential serial ports to find a connection:

/dev/ttyUSB0 - this is where a USB-UART FTDI adapter normally ends up.
/dev/ttyS0 - This is the first "true" serial port. Valid for Raspberry Pi 3.
/dev/ttyAMA0 - This is the serial port of a Raspberry Pi 1 or 2.

If a connection is find, and the FPGA board is in the other end, you can now start reception by altering frequency, mode, volume etc. Good luck!


