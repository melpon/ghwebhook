#!/bin/bash

cd /home/ghwebhook/ghwebhook
sudo -l ghwebhook git pull
stop ghwebhook
sleep 1
start ghwebhook
