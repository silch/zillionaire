import logging, os, random, re, sys, time
from appJar import gui
from pygame import mixer
import config as c

logging.basicConfig(format="%(levelname)s: %(message)s")
log = logging.getLogger("log")
log.setLevel('DEBUG') # set from INFO to DEBUG for more verbosity

def initCheck(): # check fundamentals before running anything
  if not os.path.isdir(c.saveDir): os.mkdir(c.saveDir)
  elif not os.access(c.saveDir, os.W_OK): raise Exception("Save directory is not writeable")
  if len(sys.argv) > 3: raise Exception("Too many arguments")
  elif len(sys.argv) is 2 or len(sys.argv) is 3:
    if not re.match(c.namePattern, sys.argv[1]): raise Exception("Invalid show name")
  if len(sys.argv) is 3:
    if not re.match(c.namePattern, sys.argv[2]): raise Exception("Invalid player name")

class Show:
  def __init__(self):
    self.name, self.playername = "myshow", "myplayer"
    if 2 <= len(sys.argv) <= 3: self.name = sys.argv[1]
    if len(sys.argv) is 3: self.playername = sys.argv[2]
    self.screen = Screen(self)

  def start(self, showname):
    self.name = showname
    if not re.match(c.namePattern, self.name): raise Exception("Invalid show name: "+self.name)
    self.rootDir = c.saveDir+"/"+showname+"/"
    self.unusedDir = self.rootDir+c.unusedDir+"/"
    if not os.path.isdir(self.rootDir):
      log.info("Creating new show: "+self.name)
      try: csvsource = open(c.csvSource, 'r')
      except IOError: raise Exception("Cannot read .csv input: "+c.csvSource)
      try: os.makedirs(self.unusedDir)
      except: raise Exception("Cannot create save dir")
      for linecount, line in enumerate(csvsource):
        fields = self.readLine(line)
        if fields:
          try: open(self.unusedDir+str(fields[0]), "a").write(line)
          except: raise Exception("Cannot write to file: "+self.unusedDir+str(fields[0]))
        else: log.warn("Skipping invalid line "+str(linecount+1)+" in "+c.csvSource)
      csvsource.close()
    else: log.info("Loading existing show: "+self.name)
    self.getStats()
    if self.numQuestions is 0: raise Exception("No unused questions found ")
    elif self.numQuestions < len(c.levels): self.screen.warnBox("There's not enough unused questions for completing one full round")
    elif self.dirty: self.screen.warnBox("Dirty mode activated. This happens if there are no (more) unused questions for certain difficulty levels. If such a level is reached, a question from the nearest possible level will be picked instead.")

  # calculate the number of possible games
  def getStats(self):
    self.numQuestions = 0
    self.dirty = False
    self.minNumPlayers = self.maxNumPlayers = 0
    self.numRounds = []
    for level in range(len(c.levels)):
      if not os.path.isfile(self.unusedDir+str(level+1)):
        self.dirty = True
        self.numRounds.append(0)
        continue
      self.numRounds.append(sum(1 for line in open(self.unusedDir+str(level+1))))
      if self.numRounds[level] is 0: self.dirty = True
      self.numQuestions += self.numRounds[level]
      if level is 1: self.maxNumPlayers = self.minNumPlayers = self.numRounds[level]
      elif self.numRounds[level] < self.minNumPlayers: self.minNumPlayers = self.numRounds[level]
    log.info("Total number of unused questions: "+str(self.numQuestions))
    log.info("Clean games possible: "+str(self.minNumPlayers)+" - "+str(self.maxNumPlayers))
    log.info("Dirty games possible: "+str(int(self.numQuestions/len(c.levels)))+" - "+str(self.numQuestions))

  # check a csv line for validity and return its fields as list. Return false if line is invalid
  def readLine(self, line):
    fields = line.rstrip().split(c.csvDelimiter)  
    if len(fields) != len(c.letters)+3:
      log.warn("Invalid line: Unexpected number of fields")
      return False
    for count, field in enumerate(fields):
      if count is 0: pat = "^[0-9]+$" # Round number field: numbers only, max length 2
      elif count is 1: pat = "^.{1,"+str(c.maxlenQuestion)+"}$" # Question field: max length 128 (default)
      elif 2 <= count <= len(c.letters)+1: pat = "^.{1,"+str(c.maxlenAnswer)+"}$" # Answer fields: max length 64 (default)
      elif count is len(c.letters)+2: pat = "^.{0,"+str(c.maxlenComment)+"}$" # Comment field: max length 256 (default), can be empty
      if not re.match(pat, field):
        log.debug("Invalid line: Field "+str(count)+" has too many characters")
        return False
    fields[0] = int(fields[0])
    if not 0 < fields[0] <= len(c.levels):
      log.debug("Invalid line: Invalid level number")
      return False
    return fields

  # randomly pick an unused question from "questions.csv" and move it to the player's level file.
  # if there are no more unused questions for this level, pick one from the nearest level. 
  def pickLine(self, level, dstpath):
    levels = [level] # order in which the level files are searched for a line to pick. start with current level
    for distance in range(1, len(c.levels)):
      if level - distance > 0: levels.append(level - distance)
      if level + distance <= len(c.levels): levels.append(level + distance)
    for count, level in enumerate(levels):
      srcpath = self.unusedDir+str(level)
      if count is 1: log.warn("Dirtily picking a line")
      if not os.path.exists(srcpath) or os.path.getsize(srcpath) is 0: continue
      else:
        try: lines = open(srcpath, "r").readlines()
        except: raise Exception("Cannot read file: "+srcpath)
        try: srcfile = open(srcpath, "w")
        except: raise Exception("Cannot write file: "+srcpath)
        if len(lines) is 0: raise Exception("File is empty: "+srcpath)
        pickedLineNum = random.randint(0, len(lines)-1)
        for count, line in enumerate(lines):
          if not pickedLineNum is count: srcfile.write(lines[count])
        srcfile.close()
        try: open(dstpath, "a").write(lines[pickedLineNum])
        except: raise Exception("Cannot read/write file: "+dstpath)
        log.debug("Moved line "+str(pickedLineNum+1)+" out of "+str(len(lines))+" from \""+srcpath+"\" to \""+dstpath+"\"")
        return lines[pickedLineNum]
    raise Exception("No questions left")

  def addPlayer(self, name): self.player = Player(name, self)

  def cmd(self, command): # execute commands behind the buttons on the moderator screen
    if command == "Start Show":
      if self.screen.stage == 'preshow' and s.getEntry("Input"):
        self.start(s.getEntry("Input"))
        self.screen.setStage('introshow')
      elif self.screen.stage == 'introshow': self.screen.setStage('preplayer')
      elif self.screen.stage == 'preplayer' and s.getEntry("Input"):
        try:
          self.addPlayer(s.getEntry("Input"))
          self.screen.setStage('playerstart')
        except Exception as e:
          self.screen.errorBox("Could not load player: "+str(e))
          self.screen.setStage('preplayer')
      elif self.screen.stage == 'playerstart': self.player.level.nextStage()
      elif self.screen.stage == 'playerend': self.screen.setStage('preplayer')
    elif command == "Toggle Fullscreen": self.screen.gsHandler("fullscreen", 0)
    elif command == "Toggle Sound": self.screen.toggleSound()
    elif command == "Exit":
      if self.screen.confirmBox("Do you really want to quit?"): self.exit()
    elif command == "Next Step":
      if self.player.levelnum is len(c.levels)+1: self.player.end()
      elif self.player.level.stage is 5:
        self.player.nextLevel()
      self.player.level.nextStage()
    elif command == "Info":
      infostring = "Number of games possible: "+str(self.minNumPlayers)+"-"+str(self.maxNumPlayers)
    elif command == "End Player":
      if self.player.level.stage is 5 or self.screen.confirmBox("End player?"): self.player.end()
    elif command == "End Show": self.screen.setStage('preshow')
    elif command.isdigit() and 0 <= int(command) < len(c.letters):
      self.player.level.chosen = int(command)
      if self.player.level.stage is 3: self.player.level.nextStage()
      elif self.player.level.stage is 4: self.screen.setStage("finalanswer")
    elif re.match('^Joker[0-9]+$', command):
      joker = int(re.match('^Joker([0-9]+)$', command).group(1))
      self.player.useJoker(joker)
    else: raise Exception("Unknown command: "+command)

  def exit(self):
    log.info("Exiting.")
    sys.exit(0)

class Player:
  def __init__(self, name, show):
    self.name, self.show = name, show
    self.ended, self.lost = False, False
    self.saveLevels = self.show.rootDir+self.name+".csv"
    self.saveState = self.show.rootDir+self.name+".sav"
    self.levelnum = 0
    self.jokers = []
    if os.path.isfile(self.saveLevels) and os.path.isfile(self.saveState): self.load()
    elif not os.path.isfile(self.saveLevels) and not os.path.isfile(self.saveState): self.new()
    else: raise Exception("Unexpected save state")

  def new(self):
    log.info("Adding new player: "+self.name)
    for index, joker in enumerate(c.jokers): self.jokers.append(c.jokers[index][1])
    self.writeSavegame()
    self.show.pickLine(1, self.saveLevels)
    self.load()

  def load(self):
    log.info("Loading player: "+self.name)
    try: lines = open(self.saveLevels, "r").readlines()
    except: raise Exception("Cannot read file: "+self.saveLevels)
    self.levelnum = len(lines)
    if self.levelnum is 0: raise Exception("Empty file: "+self.saveLevels)
    elif self.levelnum > len(c.levels): raise Exception("Current level higher than maximum")
    self.readSavegame()
    self.startLevel(lines[-1])

  def nextLevel(self):
    self.levelnum += 1
    if self.levelnum <= len(c.levels): self.startLevel(self.show.pickLine(self.levelnum, self.saveLevels))
    elif self.levelnum == len(c.levels)+1: self.end()
    else: raise Exception("Invalid level number")

  def startLevel(self, line):
    log.info("Starting Level "+str(self.levelnum))
    fields = self.show.readLine(line)
    if not fields: raise Exception("Invalid line")
    else: self.level = Level(fields, self)

  def readSavegame(self):
    try: savestring = open(self.saveState, "r").read().rstrip()
    except: raise Exception("Cannot read file: "+self.saveState)
    if not re.match('^[0-9]{3,4}$', savestring): raise Exception("Invalid save file: "+self.saveState)
    if len(savestring) is len(c.jokers)+1 and int(savestring[len(c.jokers)]) is 0: raise Exception("Player already lost the game")
    elif len(savestring) is len(c.jokers)+1 and int(savestring[len(c.jokers)]) is 1: raise Exception("Player already won the game")
    elif len(savestring) is len(c.jokers)+1: raise Exception("Invalid winner/loser flag in save file")
    self.jokers = []
    for index, amount in enumerate(savestring): self.jokers.append(int(amount))

  def writeSavegame(self):
    jokerline = ""
    for joker in range(0, len(c.jokers)): jokerline = jokerline+str(self.jokers[joker])
    if self.ended and self.lost: jokerline = jokerline+"0"
    elif self.ended and not self.lost: jokerline = jokerline+"1"
    try: open(self.saveState, "w").write(jokerline) 
    except OSError: raise Exception("Could not write to file: "+self.saveState)

  def useJoker(self, joker):
    if not 0 <= joker < len(c.jokers): raise Exception("Requested joker is invalid")
    if not self.hasJoker(joker):
      log.warn("Requested joker was already used")
      return
    if not self.show.screen.confirmBox("Use \""+c.jokers[joker][0]+"\" Joker?"): return
    if joker is 0: self.jokerFifty()
    elif joker is 1: self.jokerPhone()
    elif joker is 2: self.jokerAudience()
    else: raise Exception("Requested joker not implemented")    
    self.jokers[joker] -= 1
    self.writeSavegame()

  def hasJoker(self, joker):
    if self.jokers[joker] > 0: return True
    else: return False

  def jokerFifty(self):
    strikenum = round(len(c.letters) / 2)
    incorrect = []
    for answer in range(0, len(c.letters)):
      if not answer is self.level.correct: incorrect.append(answer)
    strike = random.sample(incorrect, strikenum)
    for answer in strike:
      self.show.screen.gsHandler("excludeanswer", answer)
    print("DISABLE: "+str(strike[0]))
    print("DISABLE: "+str(strike[1]))

  def jokerPhone(self):
    timetotal = 30
    steps = 100 / timetotal
    if 100 % timetotal is 0: steps -= 1
    self.show.screen.gsHandler("showcountdown", 0)
    self.show.screen.playSound("joker-phone", 0)
    for second in range(timetotal):
      self.show.screen.gsHandler("setcountdown", second*steps)
      time.sleep(0.95)
    self.show.screen.gsHandler("hidecountdown", 0)

  def jokerAudience(self):
    self.show.screen.gsHandler("splash", 1)
    while not self.show.screen.confirmBox("Show Result"): pass
    self.show.screen.playSound("joker-audience", 0)
    self.show.screen.gsHandler("splash", 0)

  def end(self):
    self.price = "0"+c.unit
    if 0 < self.level.stage <= 3: self.lost = False
    elif self.level.stage is 5:
      if self.level.isCorrect(self.level.chosen): self.lost = False
      else: self.lost = True
    else: raise Exception("Unexpected level stage to finish player")
    self.ended = True
    print("LEVEL: "+str(self.levelnum))
    if self.lost:
      print("LOST")
      for milestone in c.milestones:
        if self.levelnum - 1 >= milestone: self.price = c.levels[milestone]+c.unit
        else: break
    else:
      print("TOOK CASH")
      if self.levelnum > 1: self.price = c.levels[self.levelnum-2]+c.unit
    self.writeSavegame()
    self.show.screen.setStage("playerend")

class Level:
  def __init__(self, fields, parent):
    self.player = parent
    self.num = int(fields[0])
    self.question = fields[1]
    self.answers = [0] * len(c.letters)
    indexes = random.sample(range(0,len(c.letters)), len(c.letters))
    for count in range(0, len(c.letters)):
      self.answers[count] = fields[indexes[count]+2]
      if indexes[count] is 0: self.correct = count
    self.comment = fields[len(c.letters)+2]
    self.stage = 0
    self.chosen = -1

  def isCorrect(self, choice):
    if choice is self.correct: return 1
    else: return 0

  def nextStage(self):
    self.stage+=1
    self.setStage(self.stage)

  def setStage(self, stage): # the Level class and the Screen class both have their own stages
    if stage is 1: self.player.show.screen.setStage("levelstart")
    elif stage is 2: self.player.show.screen.setStage("showquestion")
    elif stage is 3: self.player.show.screen.setStage("showanswers")
    elif stage is 4: self.player.show.screen.setStage("finalanswer")
    elif stage is 5:
      if self.isCorrect(self.chosen): self.player.show.screen.setStage("correct")
      else: self.player.show.screen.setStage("incorrect")
    else: raise Exception("Invalid stage: "+str(stage))

class Screen:
  def __init__(self, show):
    self.show = show
    mixer.init()
    self.msDraw()
    self.gsDraw()
    self.soundOn = True
    self.stage = "preshow"
    self.setStage(self.stage)

  def msDraw(self): # draw the moderator screen
    with s.labelFrame("Main", 0, 0):
      s.setSticky("ewsn")
      s.addButton("Start Show", self.show.cmd, 0, 0)
      s.addIconButton("Toggle Fullscreen", self.show.cmd, "display", 0, 1)
      s.setButtonTooltip("Toggle Fullscreen", "Fullscreen On/Off")
      s.addIconButton("Toggle Sound", self.show.cmd, "md-sound", 0, 2)
      s.setButtonTooltip("Toggle Sound", "Sound On/Off")
      s.addIconButton("Exit", self.show.cmd, "exit", 0, 3)
      s.setButtonTooltip("Exit", "Quit program")
      s.addEntry("Input", 1, 0)
      s.setEntryAlign("Input", "center")
    with s.labelFrame("Moderator", 1, 0):
      s.setSticky("ewsn")
      s.addButton("Next Step", self.show.cmd, 0, 0)
      s.addButton("End Player", self.show.cmd, 0, 1)
      s.addButton("End Show", self.show.cmd, 0, 2)
      s.addButton("Info", self.show.cmd, 0, 3)
      s.addMessage("Details", "", 1, 0).config(anchor="w", width=c.m_scrWidth-16)
    with s.labelFrame("Round", 2, 0):
      s.setSticky("ewsn")
      s.addMessage("Question", "" , 0, 0, 3).config(width=c.m_scrWidth, anchor="w")
      for loop in range(len(c.letters)): s.addButton(str(loop), self.show.cmd, loop + 1, 0, 3).config(anchor="w")
      s.addMessage("Comment", "", len(c.letters)+3, 0, 3).config(anchor="w", width=c.m_scrWidth-16)
      with s.labelFrame("Jokers", len(c.letters)+4, 0, 3):
        for joker in range(len(c.jokers)):
          s.setSticky("ewsn")
          s.addButton("Joker"+str(joker), self.show.cmd, len(c.letters)+4, joker)
          s.setButton("Joker"+str(joker), c.jokers[joker][0])

  def gsDraw(self): # draw the game screen
    self.splash = c.imageDir+"/splash.gif"
    s.setTitle("Moderator Screen")
    s.startSubWindow("Game Screen")
    s.setLocation(0, 0)
    s.setSize(c.p_scrWidth, c.p_scrHeight)
    s.setBg("black")
    s.setFg("white")
    s.setSticky("wesn")
    with s.frame("GMain", 0, 0):
      s.setSticky("wesn")
      s.addMessage("GSeparator1", "", 0, 0)
#      s.addMessage("GTitle", "", 0, 0).config(font=(c.p_fontType, int(c.p_fontSize/2), "bold"), width=c.p_scrWidth, fg=c.p_titleColor)
      s.addMessage("GQuestion", "", 1, 0).config(font=(c.p_fontType, c.p_fontSize, "bold"), width=c.p_scrWidth-1, relief="raised")
      s.setMessagePadding("GQuestion", [2, 2])
      s.addSplitMeter("GCountdown", 2, 0).config(fill=["red", "green"])
      s.setSticky("")
      with s.frame("GAnswers", 3, 0):
        for loop in range(len(c.letters)):
          s.setSticky("w")
          with s.frame("GAnswerFrame"+str(loop), loop, 0):
            s.addMessage("GLabel"+str(loop), c.letters[loop]+": ", 0, 0).config(font=(c.p_fontType, c.p_fontSize, "bold"), fg=c.p_titleColor)
            s.addMessage("GAnswer"+str(loop), "", 0, 1).config(font=(c.p_fontType, c.p_fontSize), width=c.p_scrWidth - (2 * c.p_fontSize))
      s.addMessage("GSeparator2", "", 4, 0)
    with s.frame("GSplash", 0, 0):
      s.addImage("GSplashBlack", c.imageDir+"/splash_black.gif", 0, 0, 1, 5)
      s.addImage("GSplashStatic", c.imageDir+"/splash_static.gif", 0, 0, 1, 5)
      s.addImage("GSplashAnim", c.imageDir+"/splash_anim.gif", 0, 0, 1, 5)
      s.addMessage("GSplashPrice", "500'000$", 0, 0).config(font=(c.p_fontType, 60), width=c.p_scrWidth, fg=c.p_titleColor)
    with s.frame("GStatus", 0, 0):
      s.addMessage("GSeparator3", "", 0, 0)
      for index in range(len(c.jokers)):
        s.addImage("GJoker"+str(index), c.imageDir+"/"+c.jokers[index][0]+".gif", 1, index)
        s.addImage("GJoker"+str(index)+"X", c.imageDir+"/"+c.jokers[index][0]+"-x.gif", 1, index)
      s.addMessage("GSeparator4", "", 2, 0)
      for level in range(len(c.levels)):
        with s.frame("GLevel"+str(level+1), len(c.levels)-level+3, 1):
          s.addMessage("GLevel"+str(level+1)+"Price", str(c.levels[level])+c.unit, len(c.levels)-level, 0, 0).config(font=(c.p_fontType, int(c.p_fontSize / 2)), width=200, fg=c.p_titleColor)
          for milestone in c.milestones:
            if level == milestone-1:
              s.setMessageFg("GLevel"+str(level+1)+"Price", c.p_foregColor)
              break
      s.addMessage("GSeparator5", "", len(c.levels)+4, 0)
    s.stopSubWindow()

  def setStage(self, stage):
    if stage == 'preshow': # before the show has started
      s.setEntry("Input", self.show.name)
      s.showEntry("Input")
      s.setButton("Start Show", "Start Show")
      s.enableButton("Start Show")
      s.hideLabelFrame("Moderator")
      s.hideLabelFrame("Round")
      self.gsHandler("splash-image", 0)
      self.gsHandler("splash", 1)
      self.gsHandler("statusscreen", 0)
      self.gsHandler("show", 1)
    elif stage == 'introshow': # show has started, intro sound is played and splash screen is shown
      s.hideEntry("Input")
      s.setButton("Start Show", "Select Player")
      self.gsHandler("splash-image", 2)
      self.playSound("intro-show", 0)
    elif stage == 'preplayer': # selection of next player is in process
      s.setEntry("Input", self.show.playername)
      s.showEntry("Input")
      s.setButton("Start Show", "Add Player")
      s.enableButton("Start Show")
      s.hideLabelFrame("Moderator")
      s.hideLabelFrame("Round")
      self.gsHandler("splash-image", 1)
      self.gsHandler("splash", 1)
      self.gsHandler("statusscreen", 0)
      self.playSound("standby", 1)
    elif stage == 'playerstart': # player was selected, first level awaits
      s.setButton("Start Show", "Start Game")
      s.hideEntry("Input")
      self.gsHandler("splash-image", 2)
      self.playSound("intro-player", 0)
    elif stage == 'levelstart': # level has started, status screen is shown
      s.disableButton("Start Show")
      s.disableButton("End Player")
      s.setButton("Next Step", "Show Question")
      s.enableButton("Next Step")
      s.setMessage("Question", self.show.player.level.question)
      s.setMessage("Details", "Show: "+self.show.name+"  Player: "+self.show.player.name)
      s.setMessageTooltip("Question", c.letters[self.show.player.level.correct]+"\n\n"+self.show.player.level.comment)
      for answer in range(len(c.letters)):
        s.setButton(str(answer), c.letters[answer]+": "+self.show.player.level.answers[answer])
        s.disableButton(str(answer))
      for joker in range(len(c.jokers)):
        if self.show.player.hasJoker(joker): s.enableButton("Joker"+str(joker))
        else: s.disableButton("Joker"+str(joker))
      s.setMessage("Comment", "")
      s.hideLabelFrame("Jokers")
      s.showLabelFrame("Moderator")
      s.hideLabelFrame("Round")
      self.gsHandler("newlevel", 0)
      self.gsHandler("splash", 0)
      self.playSound("letsplay", 0)
    elif stage == 'showquestion': # question is shown
      s.setButton("Next Step", "Show Answers")
      s.setLabelFrameTitle("Round", "Round "+str(self.show.player.levelnum))
      s.showLabelFrame("Round")
      self.gsHandler("showquestion", 0)
      self.playSound("question", 1)
    elif stage == 'showanswers': # answers are shown
      for loop in range(len(c.letters)): s.enableButton(str(loop))
      s.enableButton("End Player")
      s.disableButton("Next Step")
      self.gsHandler("showanswers", 0)
      s.showLabelFrame("Jokers")
    elif stage == 'finalanswer': # answer is logged in
      s.setButton("Next Step", "Resolve")
      s.disableButton("End Player")
      s.enableButton("Next Step")
      s.setMessage("Comment", self.show.player.level.comment)
      s.hideLabelFrame("Jokers")
      self.gsHandler("selectanswer", 0)
      self.playSound("finalanswer", 0)
    elif stage == 'correct': # answer is correct
      self.gsHandler("resolve", 0)
      if self.show.player.levelnum is len(c.levels)+1: s.setButton("Next Step", "Next Player")
      else: s.setButton("Next Step", "Next Level")
      self.playSound("correct", 0)
    elif stage == 'incorrect': # answer is incorrect
      s.enableButton("End Player")
      self.gsHandler("resolve", 0)
      s.setButton("Next Step", "Cheat")
      self.playSound("incorrect", 0)
    elif stage == 'playerend': # player has won, lost, or taken the money
      self.setStage('preshow')
      s.setEntry("Input", "")
      s.hideEntry("Input")
      s.setButton("Start Show", "Next Player")
      self.gsHandler("splash-image", 3)
      self.playSound("endplayer", 0)
    else: raise Exception("Invalid stage")
    log.debug("Entering game stage \""+stage+"\"")
    self.stage = stage

  def gsHandler(self, action, arg): # display things on the game screen
    s.openSubWindow("Game Screen")
    if action == "show":
      if arg is 0: s.hideSubWindow("Game Screen")
      elif arg is 1: s.showSubWindow("Game Screen")
    elif action == "fullscreen":
      if s.fullscreen: s.exitFullscreen()
      else: s.setSize("fullscreen")
    elif action == "splash" and arg is 0: s.hideFrame("GSplash")
    elif action == "splash" and arg is 1: s.showFrame("GSplash")
    elif action == "splash-image" and 0 <= arg <=3:
      s.hideImage("GSplashBlack")
      s.hideImage("GSplashStatic")
      s.hideImage("GSplashAnim")
      s.hideMessage("GSplashPrice")
      if arg is 0: s.showImage("GSplashBlack")
      elif arg is 1: s.showImage("GSplashStatic")
      elif arg is 2: s.showImage("GSplashAnim")
      elif arg is 3:
        s.setMessage("GSplashPrice", self.show.player.price)
        s.showMessage("GSplashPrice")
    elif action == "newlevel":
#      s.setMessage("GTitle", "Question "+str(self.show.player.levelnum)+" / "+str(len(c.levels)))
      s.setMessage("GQuestion", "")
      s.hideFrame("GAnswers")
      self.gsHandler("hidecountdown", 0)
      self.gsHandler("statusscreen", 1)
    elif action == "showquestion":
      s.setMessage("GQuestion", self.show.player.level.question)
      self.gsHandler("statusscreen", 0)
    elif action == "showanswers":
      s.showFrame("GAnswers")
      for answer in range(len(c.letters)):
        s.setMessage("GAnswer"+str(answer), self.show.player.level.answers[answer])
        s.setFrameBg("GAnswerFrame"+str(answer), c.p_backgColor)
        s.showFrame("GAnswerFrame"+str(answer))
    elif action == "selectanswer":
      for loop in range(len(c.letters)): s.setFrameBg("GAnswerFrame"+str(loop), c.p_backgColor)
      s.setFrameBg("GAnswerFrame"+str(self.show.player.level.chosen), c.p_highlColor)
    elif action == "resolve": s.setFrameBg("GAnswerFrame"+str(self.show.player.level.correct), c.p_corrColor)
    elif action == "statusscreen" and arg is 0:
      s.hideFrame("GStatus")
    elif action == "statusscreen" and arg is 1:
      for level in range(len(c.levels)):
        if level+2 == self.show.player.levelnum: s.setFrameBg("GLevel"+str(level+1), c.p_corrColor)
        else: s.setFrameBg("GLevel"+str(level+1), c.p_backgColor)
      for joker in range(len(c.jokers)):
        if self.show.player.hasJoker(joker):
          s.showImage("GJoker"+str(joker))
          s.hideImage("GJoker"+str(joker)+"X")
        else:
          s.hideImage("GJoker"+str(joker))
          s.showImage("GJoker"+str(joker)+"X")
      s.showFrame("GStatus")
    elif action == "excludeanswer":
      s.hideFrame("GAnswerFrame"+str(arg))
      self.playSound("joker-fifty", 0)
    elif action == "showcountdown": s.showMeter("GCountdown")
    elif action == "hidecountdown": s.hideMeter("GCountdown")
    elif action == "setcountdown": s.setMeter("GCountdown", arg)
    else: raise Exception("Invalid action")
    s.stopSubWindow()

  def playSound(self, action, loop):
    srcdir=c.soundDir+"/"+action
    for count, suffix in enumerate(c.soundFormats):
      if os.path.isfile(srcdir+"."+suffix):
        srcfile = srcdir+"."+suffix
        break
      elif os.path.isfile(srcdir+"/"+str(self.show.player.levelnum)+"."+suffix):
        srcfile = srcdir+"/"+str(self.show.player.levelnum)+"."+suffix
        break
      elif count is len(c.soundFormats): raise Exception("Sound file not found.")
    log.debug("Playing sound file: "+srcfile)
    mixer.music.load(srcfile)
    if loop is 0: mixer.music.play()
    elif loop is 1: mixer.music.play(-1)

  def toggleSound(self):
    if self.soundOn:
      log.info("Turning sound off")
      mixer.music.pause()
      self.soundOn = False
    else:
      log.info("Turning sound on")
      mixer.music.unpause()
      self.soundOn = True

  def confirmBox(self, question):
    if s.yesNoBox("Confirmation required", question): return True
  def errorBox(self, info): s.errorBox("Error", info)
  def warnBox(self, info): s.warningBox("Warning", info)

initCheck()
s = gui(handleArgs=False)
show = Show()
s.go()


