CREATE TABLE IF NOT EXISTS guilds (
    GuildID BIGINT PRIMARY KEY,
    Prefix TEXT DEFAULT '!',
    WelcomeMessage TEXT DEFAULT 'disabled',
    WelcomeChannelID INTEGER DEFAULT 0,
    Logs TEXT DEFAULT 'disabled',
    LogsChannelID BIGINT DEFAULT 0,
    Stream TEXT DEFAULT 'disabled',
    StreamChannelID BIGINT DEFAULT 0,
    StreamPingRoleID BIGINT DEFAULT 0,
    StreamListenRoleID BIGINT DEFAULT 0,
    MutedRoleID BIGINT DEFAULT 0,
    Profanity TEXT DEFAULT 'enabled',
    Experience TEXT DEFAULT 'enabled',
    ExperienceID BIGINT DEFAULT 0,
    ProfanityList TEXT[]
    -- AutoLinks TEXT DEFAULT 'enabled',
    -- AutoLinksID BIGINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS exp (
    GuildID BIGINT NOT NULL,
    UserID BIGINT  NOT NULL,
    XP INTEGER DEFAULT 0,
    UserLevel INTEGER DEFAULT 0,
    XPLock TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (GuildID, UserID)
);