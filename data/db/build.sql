CREATE TABLE IF NOT EXISTS guilds (
    GuildID integer PRIMARY KEY,
    Prefix text DEFAULT "!",
    WelcomeMessage text DEFAULT "disabled",
    WelcomeChannelID integer DEFAULT 0,
    Logs text DEFAULT "disabled",
    LogsChannelID integer DEFAULT 0,
    MutedRoleID INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS exp (
    UserID integer PRIMARY KEY,
    XP integer DEFAULT 0,
    UserLevel integer DEFAULT 0,
    XPLock text DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mutes (
    UserID integer PRIMARY KEY,
    EndTime text
)