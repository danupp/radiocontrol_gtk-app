## GTK applet for control of the FPGA radio

Lets you connect to the FPGA radio over serial port (or I2C on a Raspberry Pi) and set frequency and other parameters. For installation instructions see [GTK-APP-HOWTO.md](GTK-APP-HOWTO.md).

It also has experimental support to work as a client for remote operation with the remote control server ( https://github.com/danupp/radiocontrol_remoteserver ).

This repository was created 2017-05-06 in order to separate the code from the legacy repository where it was bundled with the FPGA firmware.

## Changelog

2016-11-12:  
	* Added TX/RX-indication.  
	* Commented out IF freq compensation.  

2016-12-17:
	* More accurate audio control.
	* cw_tx_nomod set by default.
