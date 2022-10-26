Discord bot that rates an artifact against an optimal 6* artifact. Put the command and image in the same message.

```
-rate <image> [lvl=<level>] [<stat>=<weight> ...]
```

If you just want to use the bot in your private server, contact shrubin#1866 on discord.

#### Default Weights

ATK%, DMG%, Critical, SPD, CRIT DMG - 1
ATK - 0.5
Everything else - 0

### Options
#### Level
Compare to specified artifact level (default: 15)
```
-rate lvl=0
```

#### Weights
Set custom weights (valued between 0 and 1)
```
-rate atk=1 spd=1 atk%=0.5
```
<stat> = HP, HP%, ATK, ATK%, SPD (Speed), CR (Crit Rate), CD (Crit Damage), Status ACC%, Status RES%, DEF, DEF%

### Setup
```
python3.8 -m pip install -r requirements.txt
```
Store env variables for OCR Space and Discord in `.env`

#### Run the bot
```
python3.8 bot.py
```

#### Run one-off
Edit `url` in `artery-gear-artifact-rater.py`
```
python3.8 artery-gear-artifact-rater.py
```
"# artery-gear-artifact-rater" 
