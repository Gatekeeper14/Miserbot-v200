from datetime import date, timedelta
from database import get_db, release_db
from config import get_rank, get_station_rank, get_next_rank, STREAK_BADGES

def get_passport(uid):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("""
            SELECT username, points, invites, tier, city, country, joined_at,
                   is_supporter, supporter_expires, language, passport_number
            FROM users WHERE telegram_id=%s
        """, (uid,))
        row = cur.fetchone()
        if not row:
            return None
        username, points, invites, tier, city, country, joined_at, is_sup, sup_exp, lang, passport_num = row
        cur.execute("SELECT COUNT(*) FROM users WHERE points > %s", (points,)); global_rank = cur.fetchone()[0] + 1
        cur.execute("SELECT COUNT(*) FROM vault_access WHERE telegram_id=%s", (uid,)); vault_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM nft_ownership WHERE telegram_id=%s", (uid,)); nft_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM downloads WHERE telegram_id=%s AND purchased=TRUE", (uid,)); downloads = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM stakes WHERE telegram_id=%s AND status='active'", (uid,)); active_stakes = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM song_likes WHERE telegram_id=%s", (uid,)); liked = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(pts),0) FROM fan_points WHERE telegram_id=%s AND category='earn'", (uid,)); total_earned = cur.fetchone()[0]
        cur.execute("SELECT streak_days, last_streak_date FROM radio_state WHERE id=1"); sr = cur.fetchone()
        streak = 0
        if sr:
            sd, ld = sr
            if ld and ld >= date.today() - timedelta(days=1):
                streak = sd or 0
    finally:
        release_db(conn)

    from services.economy import get_multiplier
    display = f"@{username}" if username else str(uid)
    location = f"{city}, {country}" if city else "Not shared"
    joined = joined_at.strftime("%B %Y") if joined_at else "Unknown"
    sup_badge = "  SUPPORTER" if is_sup else ""
    multiplier = get_multiplier(uid)
    passport_num = passport_num or f"P14-{uid % 100000:05d}"
    streak_badge = ""
    for days, badge in sorted(STREAK_BADGES.items(), reverse=True):
        if streak >= days:
            streak_badge = f"  {badge}"; break

    return (
        f"PARISH 14 PASSPORT\n\n"
        f"Passport:     {passport_num}\n"
        f"Name:         {display}{sup_badge}\n"
        f"Nation Tier:  {tier}\n"
        f"Station Rank: {get_station_rank(points)}\n"
        f"MiserCoins:   {points:,}\n"
        f"Total Earned: {total_earned:,} coins\n"
        f"Global Rank:  #{global_rank}\n"
        f"Multiplier:   {multiplier}x\n"
        f"Invites:      {invites}\n"
        f"Streak:       {streak} days{streak_badge}\n"
        f"Vault:        {vault_count} unlocked\n"
        f"NFTs:         {nft_count}\n"
        f"Downloads:    {downloads}\n"
        f"Liked:        {liked} songs\n"
        f"Stakes:       {active_stakes} active\n"
        f"City:         {location}\n"
        f"Joined:       {joined}\n\n"
        f"NEXT: {get_next_rank(points)}"
    )
