# Game variables:
csvSource = "questions.csv" # valid line: difficulty level|question|correct answer|incorrect answer1|incorrect answer2|incorrect answer3|comment
csvDelimiter = "|"
unusedDir = "_unused" 
saveDir = "save" # directory where the shows are saved. each show will create a subfolder, containing show and player savegames
imageDir = "images"
soundDir = "sounds"
jokers = [['Fifty', 1], ['Phone', 1], ['Audience', 1]] # Each tuple contains the joker's name and its amount at the start of the game. Ha
levels = ["50", "100", "200", "300", "500", "1'000", "2'000", "4'000", "8'000", "16'000", "32'000", "64'000", "125'000", "500'000", "1'000'000"]
unit = "$"
milestones = [5, 10, 15] # the points achieved in these levels cannot be lost anymore
letters = ["A", "B", "C", "D"] # defines how many answers each question has. also defines letters representing the answers
soundFormats = ["ogg", "wav"] # order of sound file formats to look for
namePattern = '^[0-9a-zA-Z_-]{1,16}$' # Regular expression to validate the names of player and show
maxlenQuestion = 128
maxlenAnswer = 64
maxlenComment = 256

# Player's GUI variables:
p_scrWidth = 800
p_scrHeight = 600
p_fontSize = 30
p_fontType = "DejaVu Sans Mono"
p_backgColor = "black"
p_foregColor = "white"
p_titleColor = "orange"
p_highlColor = "blue"
p_corrColor = "green"

# Moderator's GUI variables:
m_scrWidth = 640
m_scrHeight = 480

# Internationalization:
#TODO
