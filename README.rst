ghwebhook
=========

`Post-Receive Hooks`_ を受け取って任意のコマンドを実行するサーバ。

.. _`Post-Receive Hooks`: https://help.github.com/articles/post-receive-hooks

各コマンドは root ユーザで実行されるので、外部からの情報をコマンドに利用してはならない。

設定
--------

例 ::

  melpon wandbox refs/heads/master /home/wandbox/wandbox/ghwebhook.sh

左から順に、githubユーザ名、リポジトリ名、ブランチ名、コマンドになっている。

Post-Receive Hooks によってサーバの URL が叩かれたとき、
更新のあったgithubユーザ名、リポジトリ名、ブランチ名が
設定した各データに完全に一致した場合にコマンドが実行される。
