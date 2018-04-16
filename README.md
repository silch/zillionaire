# zillionaire
A party game inspired by the TV show "Who Wants to Be a Millionaire", written in Python, using [appJar](https://appjar.info) and [pygame](https://www.pygame.org).  

## Features
- Control panel: Program window used by the moderator to control the game stages such as starting the show, adding a new player, displaying the question and answers, logging in the player's final answer, activating jokers, and so on. It is intended to run on the computer's primary screen. [[screenshots/001.jpg]]  
- Game screen: Program window shown to the player and/or audience. It is intended to run on a second screen such as a TV or a projector. [[screenshots/002.jpg]]  
- Import your own questions, define their difficulty, and add comments to be displayed for the moderator during the show.
- Fonts, sound and splash screens were chosen with the original show in mind

## Restrictions
- The phone joker requires the player or the moderator to manually use a telephone (or pick someone from the audience)
- The audience joker can be chosen, but it doesn't do anything. Votes need to be manually counted and shown to the player/audience.

## Requirements
- Python 3 with Tkinter and pygame
- A computer with two displays and the ability to drag windows between them
- The game has only been tested on Ubuntu 16.04 so far, but it should work on other Linux distros and might even do so on Windows/MacOS

## Installation
### Ubuntu 16.04
> apt-get install python3-tk python3-pip #libfreetype6-dev  
> python3 -m pip install -U pygame --user  

## Preparing the questions
### Method 1: Libreoffice Calc
Open the file [[questions.csv]] in LibreOffice Calc, which will prompt you with the "Text Import" dialogue. Under "Separator Options", tick the "Other" box and type the character `|` into the field next to it. Untick all other boxes in the same row, and finally click OK.

You will see a list of example questions. They were taken from [here](https://gamefaqs.gamespot.com/gba/919785-who-wants-to-be-a-millionaire-2nd-edition/faqs/40044) for demonstration purposes. Change anything to your liking. This is what the columns stand for:  
A: Difficulty level. Put in a number from 1 to 15, where 1 is the easiest and 15 is the hardest. If multiple questions have the same difficulty level, the program will randomly pick one during the show. If there are no questions for a difficulty level, the program will pick one from the nearest available levels during the show.  
B: Question. Maximum number of characters: 128  
C: Correct answer: Maximum number of characters: 64  
D-F: Incorrect answers: Maximum number of characters: 64  
G: Comment. This will be displayed to the moderator during the show. It is intended to provide additional information about the topic for tension building or small talk purposes. It is the only field that can be left empty. Maximum number of characters: 256

When saving the file, make to you to choose the .csv format when prompted.

### Method 2: Manually using a text editor
Instead of using LibreOffice, you can simply open the file [[questions.csv]] in a text editor, using `|` as a field separator. If you don't add a comment, note that putting `|` at the end of the line is required.

## Usage
In a terminal, go to the game's root directory and run it with:  
> python3 zillionaire.py

You can optionally define the show's and the first player's names like this:  
> python3 zillionaire.py MyShow FirstPlayer

Drag the game screen window to your second display (monitor, TV, projector, ...) and hit the Fullscreen button in the control panel.

## Customization

## TODO
- Support multiple game screens, so the player doesn't have to share one with the audience
- Splash animations for winning/losing
- Add a commandline- and/or web-based control panel, so the game can be controlled remotely without the need of a dualscreen setup
- Option for the moderator to see players'/show's statistics
- Phone joker via VOIP?
- Audience joker via smartphone app?
- Integrating live video/audio stream for recording a show?

## Troubleshooting

### ALSA lib underrun
If the error message  
`ALSA lib pcm.c:7963:(snd_pcm_recover) underrun occurred`  
keeps appearing in the terminal, the reason might be a missing `pulseaudio` package. On Debian-based systems, install it with  
> apt-get install pulseaudio
If the issue persists after a reboot, [this guide](https://retro64xyz.github.io/computers/2017/05/26/how-to-fix-audacity-underrun/) might help.
