"""
Database Seeding Script for My K-Drama 2.0
Populates the database with realistic sample metadata for top Korean dramas,
including seasons, episodes, sample Telegram file references, and global settings.
"""
import asyncio
from datetime import datetime
from shared.database.connection import DatabaseConnectionManager
from shared.database.indexes import ensure_all_indexes
from shared.database.repositories import (
    dramas_repo, seasons_repo, episodes_repo, telegram_files_repo,
    bot_settings_repo, web_settings_repo, admins_repo, users_repo
)
from shared.database.schemas import (
    DramaSchema, SeasonSchema, EpisodeSchema, TelegramFileSchema,
    CastMember
)
from shared.config.settings import settings
from logging_helper import LOGGER

SAMPLE_DRAMAS = [
    {
        "drama_id": "queen-of-tears",
        "tmdb_id": 218230,
        "title": "Queen of Tears",
        "korean_title": "눈물의 여왕",
        "romanized_title": "Nunmului Yeowang",
        "alt_titles": ["Queen of Tears", "Nunmul-ui Yeowang"],
        "synopsis": "The queen of department stores and her small-town husband weather a marital crisis — until love miraculously begins to bloom again.",
        "status": "completed",
        "release_year": 2024,
        "air_date": "2024-03-09",
        "end_date": "2024-04-28",
        "genres": ["Drama", "Romance", "Comedy"],
        "tags": ["Chaebol", "Enemies to Lovers", "Marriage", "Family Crisis"],
        "network": "tvN",
        "rating_average": 8.8,
        "rating_count": 4820,
        "poster_url": "https://image.tmdb.org/t/p/w500/2m1hi0nf99pq1fpXjWzHupYJmX.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/jBJW5oxSyIfjwRbO1qVgf3g0Pox.jpg",
        "total_seasons": 1,
        "total_episodes": 16,
        "cast": [
            CastMember(name="Kim Soo-hyun", character="Baek Hyun-woo"),
            CastMember(name="Kim Ji-won", character="Hong Hae-in"),
            CastMember(name="Park Sung-hoon", character="Yoon Eun-sung"),
            CastMember(name="Kwak Dong-yeon", character="Hong Soo-cheol"),
        ]
    },
    {
        "drama_id": "crash-landing-on-you",
        "tmdb_id": 94796,
        "title": "Crash Landing on You",
        "korean_title": "사랑의 불시착",
        "romanized_title": "Sarangui Bulsichak",
        "alt_titles": ["CLOY", "Love's Emergency Landing"],
        "synopsis": "A paragliding mishap drops a South Korean heiress into North Korea - and into the life of an army officer, who decides he will help her hide.",
        "status": "completed",
        "release_year": 2019,
        "air_date": "2019-12-14",
        "end_date": "2020-02-16",
        "genres": ["Romance", "Drama", "Comedy"],
        "tags": ["North Korea", "Cross-Border Romance", "Military", "Billionaire"],
        "network": "tvN",
        "rating_average": 9.1,
        "rating_count": 8940,
        "poster_url": "https://image.tmdb.org/t/p/w500/mCRy8j2b4nZ3r2xP3Q1wG8r9P9.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/m9PGe25V8BqUo7xG9kL4r8P2n.jpg",
        "total_seasons": 1,
        "total_episodes": 16,
        "cast": [
            CastMember(name="Hyun Bin", character="Ri Jeong-hyeok"),
            CastMember(name="Son Ye-jin", character="Yoon Se-ri"),
            CastMember(name="Seo Ji-hye", character="Seo Dan"),
            CastMember(name="Kim Jung-hyun", character="Gu Seung-jun"),
        ]
    },
    {
        "drama_id": "lovely-runner",
        "tmdb_id": 242045,
        "title": "Lovely Runner",
        "korean_title": "선재 업고 튀어",
        "romanized_title": "Seonjae Eopgo Twieo",
        "alt_titles": ["Time Walking on Memory", "Run Away With Sunjae On Piggyback"],
        "synopsis": "A passionate fangirl devastated by the death of her favorite idol travels back 15 years into the past to save his life.",
        "status": "completed",
        "release_year": 2024,
        "air_date": "2024-04-08",
        "end_date": "2024-05-28",
        "genres": ["Romance", "Fantasy", "Comedy", "Time Travel"],
        "tags": ["Idol", "High School", "Destiny", "First Love"],
        "network": "tvN",
        "rating_average": 8.9,
        "rating_count": 3120,
        "poster_url": "https://image.tmdb.org/t/p/w500/1xJ2q6mG8r8P3nL9k4r8P2n9.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/8rP2n9mG8r8P3nL9k4r8P2n9.jpg",
        "total_seasons": 1,
        "total_episodes": 16,
        "cast": [
            CastMember(name="Byeon Woo-seok", character="Ryu Sun-jae"),
            CastMember(name="Kim Hye-yoon", character="Im Sol"),
            CastMember(name="Song Geon-hee", character="Kim Tae-sung"),
            CastMember(name="Lee Seung-hyub", character="Baek In-hyuk"),
        ]
    },
    {
        "drama_id": "goblin",
        "tmdb_id": 67915,
        "title": "Guardian: The Lonely and Great God",
        "korean_title": "쓸쓸하고 찬란하神 - 도깨비",
        "romanized_title": "Dokkaebi",
        "alt_titles": ["Goblin", "The Lonely and Great God - Goblin"],
        "synopsis": "In his quest for a bride to break his immortal curse, a 939-year-old guardian of souls meets a grim reaper and a sprightly student with a tragic past.",
        "status": "completed",
        "release_year": 2016,
        "air_date": "2016-12-02",
        "end_date": "2017-01-21",
        "genres": ["Fantasy", "Romance", "Drama"],
        "tags": ["Immortality", "Bromance", "Supernatural", "Reincarnation"],
        "network": "tvN",
        "rating_average": 9.2,
        "rating_count": 12400,
        "poster_url": "https://image.tmdb.org/t/p/w500/t7n8p2r9mG8r8P3nL9k4r8P2n.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/q9P2n9mG8r8P3nL9k4r8P2n.jpg",
        "total_seasons": 1,
        "total_episodes": 16,
        "cast": [
            CastMember(name="Gong Yoo", character="Kim Shin / Goblin"),
            CastMember(name="Kim Go-eun", character="Ji Eun-tak"),
            CastMember(name="Lee Dong-wook", character="Wang Yeo / Grim Reaper"),
            CastMember(name="Yoo In-na", character="Sunny / Kim Sun"),
        ]
    }
]

async def seed_database():
    LOGGER.info("Starting database seeding for My K-Drama 2.0...")
    await DatabaseConnectionManager.connect()
    await ensure_all_indexes()

    # 1. Seed Global Web Settings & Bot Settings
    await web_settings_repo.update_web_settings({
        "site_name": "My K-Drama 2.0",
        "registration_enabled": True,
        "guest_streaming_enabled": False,
        "featured_drama_ids": ["queen-of-tears", "crash-landing-on-you", "lovely-runner"]
    })
    LOGGER.info("✅ Global Web Settings initialized.")

    if settings.ADMINS:
        for admin_tg_id in settings.ADMINS:
            admin_user = await users_repo.upsert_telegram_user(
                telegram_id=admin_tg_id,
                first_name="SuperAdmin",
                username="AdminUser"
            )
            await admins_repo.add_admin(
                user_id=admin_user["_id"],
                telegram_id=admin_tg_id,
                role="superadmin",
                permissions=["manage_requests", "manage_dramas", "manage_files", "manage_users", "view_analytics", "system_settings"]
            )
        LOGGER.info(f"✅ Initialized {len(settings.ADMINS)} SuperAdmins from configuration.")

    # 2. Seed Dramas, Seasons, Episodes, and File References
    for d in SAMPLE_DRAMAS:
        drama_data = d.copy()
        drama_id = drama_data["drama_id"]

        # Upsert Drama
        drama_doc = await dramas_repo.upsert_drama(DramaSchema(**drama_data))
        LOGGER.info(f"Seeded Drama: {drama_doc['title']}")

        # Seed Season 1
        season_id = f"{drama_id}:s1"
        season_doc = await seasons_repo.upsert_season(SeasonSchema(
            season_id=season_id,
            drama_id=drama_id,
            season_number=1,
            title="Season 1",
            episode_count=drama_data["total_episodes"]
        ))

        # Seed Sample Episodes (1 to 16)
        for ep_num in range(1, drama_data["total_episodes"] + 1):
            ep_id = f"{drama_id}:s1:e{ep_num}"
            file_id_720p = f"file_{drama_id}_s01e{ep_num:02d}_720p"
            file_id_1080p = f"file_{drama_id}_s01e{ep_num:02d}_1080p"

            # Create Episode
            await episodes_repo.upsert_episode(EpisodeSchema(
                episode_id=ep_id,
                drama_id=drama_id,
                season_id=season_id,
                season_number=1,
                episode_number=ep_num,
                title=f"Episode {ep_num}",
                duration_minutes=70,
                telegram_file_ids=[file_id_720p, file_id_1080p]
            ))

            # Create corresponding mock Telegram Files in database
            await telegram_files_repo.create(TelegramFileSchema(
                _id=file_id_720p,
                file_unique_id=f"uniq_{drama_id}_s1e{ep_num}_720",
                file_name=f"{drama_doc['title']}.S01E{ep_num:02d}.720p.WEB-DL.mkv",
                clean_name=f"{drama_doc['title']} S01E{ep_num:02d} 720p",
                file_size=750 * 1024 * 1024,
                drama_id=drama_id,
                season_number=1,
                episode_number=ep_num,
                quality="720p",
                audio_languages=["Korean"],
                subtitle_languages=["English", "Hindi"]
            ))

            await telegram_files_repo.create(TelegramFileSchema(
                _id=file_id_1080p,
                file_unique_id=f"uniq_{drama_id}_s1e{ep_num}_1080",
                file_name=f"{drama_doc['title']}.S01E{ep_num:02d}.1080p.HDRip.mkv",
                clean_name=f"{drama_doc['title']} S01E{ep_num:02d} 1080p",
                file_size=1500 * 1024 * 1024,
                drama_id=drama_id,
                season_number=1,
                episode_number=ep_num,
                quality="1080p",
                audio_languages=["Korean"],
                subtitle_languages=["English", "Hindi"]
            ))

    LOGGER.info("🎉 Database seeding completed successfully with sample dramas, seasons, episodes, and files!")
    await DatabaseConnectionManager.disconnect()

if __name__ == "__main__":
    asyncio.run(seed_database())
