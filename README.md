Nebula
======

Nebula is media asset management and workflow automation system for TV and radio broadcast. 


Key features
------------
 
 - media asset management, metadata handling
 - conversion, video and audio normalization using Themis library
 - programme planning, scheduling
 - playout control (CasparCG and Liquidsoap)
 - dynamic CG (nxcg)
 - web publishing
 - statistics


Installation
------------

### Prerequisities

 - Debian Jessie
 - ffmpeg (media processing nodes) - use inst.ffmpeg.sh script
 - nginx (core node) - use inst.nginx.sh script
 
### Installation


```bash
cd /opt
git clone https://github.com/immstudios/nebula
```

### Starting 

```bash
cd /opt/nebula && ./nebula.py
```

Preffered way is to start Nebula in GNU Screen, but it is also possible to start Nebula as a Linux daemon.

```bash
cd /opt/nebula && ./nebula.py -d
```


Need help?
----------

Community version support is not provided directly by imm studios. 

Professional support for Nebula is provided to organisations with support contract.
On site installation and support is available via our Czech (support.prague@immstudios.org) and New Zealand (support.christchurch@immstudios.org) offices.

