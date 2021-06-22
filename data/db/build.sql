CREATE TABLE IF NOT EXISTS guilds (
    GuildID BIGINT PRIMARY KEY,
    Prefix TEXT DEFAULT '!',
    WelcomeMessage TEXT DEFAULT 'disabled',
    WelcomeChannelID BIGINT DEFAULT 0,
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
    ProfanityList TEXT[],
    Modmail TEXT DEFAULT 'disabled',
    ModmailCategoryID BIGINT DEFAULT 0,
    ModmailNotificationID BIGINT DEFAULT 0,
    Moderation TEXT DEFAULT 'enabled'
    -- AutoLinks TEXT DEFAULT 'enabled',
    -- AutoLinksID BIGINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS exp (
    GuildID BIGINT NOT NULL,
    UserID BIGINT  NOT NULL,
    XP INTEGER DEFAULT 0,
    UserLevel INTEGER DEFAULT 0,
    XPLock TEXT,
    PRIMARY KEY (GuildID, UserID)
);

CREATE TABLE IF NOT EXISTS modmail (
    UserID BIGINT PRIMARY KEY,
    CurrentTicketID BIGINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS blacklist (
    GuildID BIGINT NOT NULL,
    UserID BIGINT  NOT NULL,
    PRIMARY KEY (GuildID, UserID)
);