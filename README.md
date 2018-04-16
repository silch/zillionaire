# zillionaire
A party game inspired by the TV show "Who Wants to Be a Millionaire", written in Python, using [appJar](https://appjar.info) and [pygame](https://www.pygame.org). The program will open two windows: The game screen to be shown to the player/audience, and the control panel for the moderator.  

## Requirements
- Python 3
- A computer with two displays and the ability to drag windows between them

## Installation
### Ubuntu 16.04

> apt-get install python3-tk python3-pip #libfreetype6-dev  
> python3 -m pip install -U pygame --user  

## Preparing the questions
The game does not come with any pre-defined questions - you'll have to come up with some on your own. Put them in a plain text file called `questions.csv` in the program's root directory. Each line stands for one question and consists of 7 fields (difficulty level, question, correct answer, incorrect answer 1, incorrect answer 2, incorrect answer 3, comment) which are separated by the character `|`. A valid line would look like this:
> 1|What colour is lava?|Red|Blue|Green|Purple|Beneath the surface it's called magma

You can also create your list in Libreoffice Calc, filling the rows and columns in the aforementioned order. Under "Save as", choose the format "Text CSV (.csv)", and in the subsequent dialog put `|` under "Field delimiter" and remove anything under "Text delimiter". 

## Usage
You drag the game screen window to your second display (monitor, TV, projector, ...) and hit the Fullscreen button in the control panel.
