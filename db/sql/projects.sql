CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    "fundsRaised" REAL,
    "shortDescription" TEXT NOT NULL,
    description TEXT,
    "teamTelegramHandle" TEXT,
    "bannerImgUrl" TEXT NOT NULL,
    "isLaunched" BOOLEAN NOT NULL
);

CREATE TABLE "projectTeams" (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    "profileImgUrl" TEXT,
    "projectId" INT NOT NULL,
    CONSTRAINT fk_project_teams FOREIGN KEY("projectId") REFERENCES projects(id)
);

INSERT INTO
    projects(
        name,
        "shortDescription",
        "teamTelegramHandle",
        "bannerImgUrl",
        "isLaunched"
    )
VALUES
    (
        'SigmaSwap Decentralized Exchange',
        'ErgoPad''s own decentralized exchange on the Ergo blockchain.',
        'https://t.me/ergopad_chat',
        'https://raw.githubusercontent.com/ergo-pad/ergopad/main/frontend/public/projects/crypto-coins.jpg',
        false
    );

INSERT INTO
    projects(
        name,
        "shortDescription",
        "teamTelegramHandle",
        "bannerImgUrl",
        "isLaunched"
    )
VALUES
    (
        'NFT Game',
        'An NFT game where you can play to earn, rather than pay to play.',
        'https://t.me/ergopad_chat',
        'https://raw.githubusercontent.com/ergo-pad/ergopad/main/frontend/public/projects/nft-game.jpg',
        false
    );

INSERT INTO
    projects(
        name,
        "shortDescription",
        "teamTelegramHandle",
        "bannerImgUrl",
        "isLaunched"
    )
VALUES
    (
        'Decentralized Social Platform',
        'A social media platform where users are given control of their data, and are paid by advertisers directly. You''re the commodity, may as well keep all the value you provide.',
        'https://t.me/ergopad_chat',
        'https://raw.githubusercontent.com/ergo-pad/ergopad/main/frontend/public/projects/social-media-platforms.jpg',
        false
    );

ALTER TABLE projects 
RENAME "teamTelegramHandle" TO socials;
