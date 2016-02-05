# SDP 2016 Group 15-H
![Alt text](https://cloud.githubusercontent.com/assets/7432996/12533848/fec57256-c237-11e5-97d0-3df21cdc3efa.png "Project Venus")

## Setup

    git clone https://github.com/julijonas/venus.git
    cd venus
    virtualenv --system-site-packages env
    source env/bin/activate
    pip install -r requirements.txt

## Running

The project is run by entering the virtual environment `source env/bin/activate` and then executing `python main.py` in the root directory.
Then typing `connect` connects to the RF stick and typing `vision 0` starts the vision feed to the room 0 (the nearer one).
This is not done automatically so that the vision system would be integrated into our control code but at the same time one working with vision would not need to have RF stick plugged in and it would not crash, and vice versa.
