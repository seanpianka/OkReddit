# OkReddit
A reddit bot which replies to user's comments containing "ok reddit define x" with the definition of x.

This bot is akin to Google's "Google Now" software, present on many android devices today, where the user says "Ok Google, define word" and Google responds with the definition of the word in its possible numerous forms. OkReddit bot aims to reproduce this behavior on the popular website [Reddit](http://reddit.com).

#### Example usage of Google's service:

<img src="https://puu.sh/r9fcZ/226b1c46ff.png">

#### Example usage of OkReddit:

<img src="https://puu.sh/r9fAG/f844a3d9dc.png">

### Instructions

The assumptions here are that you have a working installation of Python 3 and are working in a Linux/UNIX command-line environment (the commands below are specified for such an environment). 

###### New to Linux?

If you are unfamiliar with Linux and would like to install a beginner distribution in order to run this bot continuously, check out the [Ubuntu documentation](http://www.ubuntu.com/download/desktop/create-a-usb-stick-on-windows) or the [Linux Mint documentation](https://itsfoss.com/guide-install-linux-mint-16-dual-boot-windows/) for good starter Linux distributions. 

Also, check out the YouTube channel [tutorialLinux](https://www.youtube.com/channel/UCvA_wgsX6eFAOXI8Rbg_WiQ/videos?flow=grid&view=0&sort=p) for helpful videos on how to get started, comfortable, and fast when using Linux.

###### Installation on a working copy of Linux or OS X.

`$ git clone https://github.com/seanpianka/OkReddit.git`

`$ cd OkReddit`

`$ pip install -r requirements.txt`

`$ python3 okreddit.py`

At this step, you may want to use bash (or modify the okreddit.py script yourself) to run in a "while true; do" loop so that the script runs continuously. Use the following bash commands to do so:

`while true; do python3 okreddit.py; done`

### Inspiration

[This](https://www.reddit.com/r/RequestABot/comments/51v8rg/bot_that_responds_to_a_sentence_with_the_google/) post on Reddit by [/u/CorvetteCole](//www.reddit.com/user/CorvetteCole) was the inspiration for this project.

<img src="https://i.imgur.com/QJ5wiLI.png">
