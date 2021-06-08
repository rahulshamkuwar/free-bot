CREATE TABLE IF NOT EXISTS guilds (
    GuildID INTEGER PRIMARY KEY,
    Prefix TEXT DEFAULT "!",
    WelcomeMessage TEXT DEFAULT "disabled",
    WelcomeChannelID INTEGER DEFAULT 0,
    Logs TEXT DEFAULT "disabled",
    LogsChannelID INTEGER DEFAULT 0,
    MutedRoleID INTEGER DEFAULT 0,
    Profanity TEXT DEFAULT "enabled",
    Experience TEXT DEFAULT "enabled",
    ExperienceID INTEGER DEFAULT 0
    -- AutoLinks TEXT DEFAULT "enabled",
    -- AutoLinksID INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS exp (
    GuildID INTEGER NOT NULL,
    UserID INTEGER  NOT NULL,
    XP INTEGER DEFAULT 0,
    UserLevel INTEGER DEFAULT 0,
    XPLock TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (GuildID, UserID)
);

CREATE TABLE IF NOT EXISTS mutes (
    UserID INTEGER PRIMARY KEY,
    EndTime TEXT
);