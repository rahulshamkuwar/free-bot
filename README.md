# Freebot
Free, open source Discord chat bot

## Prefix
The default prefix of the bot is `!` but it can be changed to anything using the `prefix` command. Do note that the prefix cannot be longer than 5 characters.

## Moderation
The bot currently has basic moderation tools like `ban`, `tempban`, `kick`, `mute`, `unmute`, and`clear`. I will add more info about this later, but for the mean time you can get more info by typing `help` to see all the commands and their description or `help <command name>` to get help with a specific command.
Also note that the `unban` and `muted-role` are kind of broken and will not work. Need to work on it, but seems like some issue with the database.

## Experience
The bot can keep track of user experience and rank in the guild. It is enabled by default but can be disabled by using `exp`. You can also set up a specific channel to send messages when a user levels up by using `expchannel`. By default the message is sent to the channel where the user's last sent message was. Users can also check their own and other user's rank and level with the `rank` and `level` commands. If you want to remove the channel for exp, you can use `remexpchannel`.

## Help
Running `help` will display all commands and how to use them. Running `help <command name>` will show how to use the specific command.

## Info
The bot can also show user info and server info with `userinfo` and `serverinfo` respectively. If no user is give for `userinfo` it will so the information of the author of the message.

## Logs
Logs can be enabled using `logs <enabled | disabled> <channel>` which will show messages what users edited, deleted, and when their nickname or roles changes. It also logs when users join and leave the server, kind of broken right now since Discord is not recognizing `on_member_join` and `on_member_remove` events

## Welcome
The bot can send welcome messages when a user joins the guild. Kind of buggy right now since Discord is not recognizing `on_member_join` and `on_member_remove` events. The bot requires a channel to set for sending teh welcome messages.

## Lastly

I still plan on working on this bot and improving it, once I think it's in good shape I'll probably add the invite link for the bot here. Also, this readme is a work in progress lol, it will be more fleshed out when I'm done.
