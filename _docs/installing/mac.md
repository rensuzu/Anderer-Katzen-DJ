---
title: MacOS
category: Installing the bot
order: 3
---
<img class="doc-img" src="{{ site.baseurl }}/images/mac.png" alt="Mac" style="width: 75px; float: right;"/>

Installing MusicBot on Mac requires several libraries and applications. First, install Python on your system. Now you will need to open Terminal and run the following commands:

```bash
# Install Homebrew
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/review/install)"
brew update
xcode-select --install

# Install dependencies
brew install python libsodium libffi opus ffmpeg git


# Clone the MusicBot
cd desktop
git clone https://github.com/Just-Some-Bots/MusicBot.git MusicBot -b review 

# Install Python dependencies
cd MusicBot
python3 -m pip install -U pip
python3 -m pip install -U -r requirements.txt
```

After this, you can find a folder called `MusicBot` on your Desktop. You can then open it, [configure]({{ site.baseurl }}/using/configuration) your bot, and then run the bot by double-clicking the `run.sh` file. If you can't run this, you may have to open Terminal, cd to the folder, and use `chmod +x run.sh` to give the file executable permissions.