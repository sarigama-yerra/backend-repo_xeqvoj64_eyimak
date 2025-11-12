import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel
from database import db, create_document, get_documents
from datetime import datetime

app = FastAPI(title="IPL Encyclopedia API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- Helpers ---------
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


def serialize_doc(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id")) if doc.get("_id") else None
    # Convert datetime to isoformat
    for k, v in list(doc.items()):
        if isinstance(v, datetime):
            doc[k] = v.isoformat()
    return doc


# --------- Seed Data (minimal, expandable) ---------
TEAMS_SEED = [
    {
        "name": "Chennai Super Kings",
        "slug": "chennai-super-kings",
        "short_name": "CSK",
        "logo": "https://upload.wikimedia.org/wikipedia/en/2/2f/Chennai_Super_Kings_Logo.svg",
        "colors": ["#F9CD05", "#0B5ED7"],
        "home_ground": "M. A. Chidambaram Stadium, Chennai",
        "city": "Chennai",
        "captain": "MS Dhoni",
        "head_coach": "Stephen Fleming",
        "owners": ["Chennai Super Kings Cricket Ltd"],
        "website": "https://www.chennaisuperkings.com/",
        "twitter": "https://twitter.com/ChennaiIPL",
        "instagram": "https://www.instagram.com/chennaiipl/",
        "achievements": ["IPL Champions: 2010, 2011, 2018, 2021, 2023"],
        "records": []
    },
    {
        "name": "Mumbai Indians",
        "slug": "mumbai-indians",
        "short_name": "MI",
        "logo": "https://upload.wikimedia.org/wikipedia/en/2/25/Mumbai_Indians_Logo.svg",
        "colors": ["#004BA0", "#E5C100"],
        "home_ground": "Wankhede Stadium, Mumbai",
        "city": "Mumbai",
        "captain": "Hardik Pandya",
        "head_coach": "Mark Boucher",
        "owners": ["Indiawin Sports"],
        "website": "https://www.mumbaiindians.com/",
        "twitter": "https://twitter.com/mipaltan",
        "instagram": "https://www.instagram.com/mumbaiindians/",
        "achievements": ["IPL Champions: 2013, 2015, 2017, 2019, 2020"],
        "records": []
    },
    {
        "name": "Royal Challengers Bengaluru",
        "slug": "royal-challengers-bengaluru",
        "short_name": "RCB",
        "logo": "https://upload.wikimedia.org/wikipedia/en/0/09/Royal_Challengers_Bangalore_Logo.svg",
        "colors": ["#DA2128", "#000000", "#B09A57"],
        "home_ground": "M. Chinnaswamy Stadium, Bengaluru",
        "city": "Bengaluru",
        "captain": "Faf du Plessis",
        "head_coach": "Andy Flower",
        "owners": ["United Spirits"],
        "website": "https://www.royalchallengers.com/",
        "twitter": "https://twitter.com/RCBTweets",
        "instagram": "https://www.instagram.com/royalchallengers.bengaluru/",
        "achievements": ["Runners-up: 2009, 2011, 2016"],
        "records": []
    },
    {
        "name": "Kolkata Knight Riders",
        "slug": "kolkata-knight-riders",
        "short_name": "KKR",
        "logo": "https://upload.wikimedia.org/wikipedia/en/4/4c/Kolkata_Knight_Riders_Logo.svg",
        "colors": ["#3A225D", "#D9A928"],
        "home_ground": "Eden Gardens, Kolkata",
        "city": "Kolkata",
        "captain": "Shreyas Iyer",
        "head_coach": "Chandrakant Pandit",
        "owners": ["Knight Riders Sports Pvt Ltd"],
        "website": "https://www.kkr.in/",
        "twitter": "https://twitter.com/KKRiders",
        "instagram": "https://www.instagram.com/kkriders/",
        "achievements": ["IPL Champions: 2012, 2014, 2024"],
        "records": []
    },
    {
        "name": "Rajasthan Royals",
        "slug": "rajasthan-royals",
        "short_name": "RR",
        "logo": "https://upload.wikimedia.org/wikipedia/en/6/60/Rajasthan_Royals_Logo.svg",
        "colors": ["#EA1A85", "#004BA0"],
        "home_ground": "Sawai Mansingh Stadium, Jaipur",
        "city": "Jaipur",
        "captain": "Sanju Samson",
        "head_coach": "Kumar Sangakkara",
        "owners": ["Royals Sports Group"],
        "website": "https://www.rajasthanroyals.com/",
        "twitter": "https://twitter.com/rajasthanroyals",
        "instagram": "https://www.instagram.com/rajasthanroyals/",
        "achievements": ["IPL Champions: 2008"],
        "records": []
    },
    {
        "name": "Sunrisers Hyderabad",
        "slug": "sunrisers-hyderabad",
        "short_name": "SRH",
        "logo": "https://upload.wikimedia.org/wikipedia/en/8/81/Sunrisers_Hyderabad.png",
        "colors": ["#F26522", "#000000"],
        "home_ground": "Rajiv Gandhi Intl. Cricket Stadium, Hyderabad",
        "city": "Hyderabad",
        "captain": "Pat Cummins",
        "head_coach": "Daniel Vettori",
        "owners": ["Sun TV Network"],
        "website": "https://www.sunrisershyderabad.in/",
        "twitter": "https://twitter.com/SunRisers",
        "instagram": "https://www.instagram.com/sunrisershyd/",
        "achievements": ["IPL Champions: 2016"],
        "records": []
    },
    {
        "name": "Delhi Capitals",
        "slug": "delhi-capitals",
        "short_name": "DC",
        "logo": "https://upload.wikimedia.org/wikipedia/en/2/2f/Delhi_Capitals.svg",
        "colors": ["#004BA0", "#EA1A85"],
        "home_ground": "Arun Jaitley Stadium, Delhi",
        "city": "Delhi",
        "captain": "Rishabh Pant",
        "head_coach": "Ricky Ponting",
        "owners": ["GMR Group", "JSW Group"],
        "website": "https://www.delhicapitals.in/",
        "twitter": "https://twitter.com/DelhiCapitals",
        "instagram": "https://www.instagram.com/delhicapitals/",
        "achievements": ["Runners-up: 2020"],
        "records": []
    },
    {
        "name": "Punjab Kings",
        "slug": "punjab-kings",
        "short_name": "PBKS",
        "logo": "https://upload.wikimedia.org/wikipedia/en/d/d4/Punjab_Kings_Logo.svg",
        "colors": ["#ED1B24", "#CBA92B"],
        "home_ground": "PCA Stadium, Mohali",
        "city": "Mohali",
        "captain": "Shikhar Dhawan",
        "head_coach": "Trevor Bayliss",
        "owners": ["KPH Dream Cricket Pvt. Ltd"],
        "website": "https://www.punjabkingsipl.in/",
        "twitter": "https://twitter.com/PunjabKingsIPL",
        "instagram": "https://www.instagram.com/punjabkingsipl/",
        "achievements": ["Runners-up: 2014"],
        "records": []
    },
    {
        "name": "Gujarat Titans",
        "slug": "gujarat-titans",
        "short_name": "GT",
        "logo": "https://upload.wikimedia.org/wikipedia/en/8/8d/Gujarat_Titans_Logo.svg",
        "colors": ["#0B5ED7", "#B09A57"],
        "home_ground": "Narendra Modi Stadium, Ahmedabad",
        "city": "Ahmedabad",
        "captain": "Shubman Gill",
        "head_coach": "Ashish Nehra",
        "owners": ["CVC Capital Partners"],
        "website": "https://www.gujarattitansipl.com/",
        "twitter": "https://twitter.com/gujarat_titans",
        "instagram": "https://www.instagram.com/gujarat_titans/",
        "achievements": ["IPL Champions: 2022", "Runners-up: 2023"],
        "records": []
    },
    {
        "name": "Lucknow Super Giants",
        "slug": "lucknow-super-giants",
        "short_name": "LSG",
        "logo": "https://upload.wikimedia.org/wikipedia/en/4/4c/Lucknow_Super_Giants_Logo.svg",
        "colors": ["#00B3B3", "#F26522", "#F9CD05"],
        "home_ground": "BRSABV Ekana Cricket Stadium, Lucknow",
        "city": "Lucknow",
        "captain": "KL Rahul",
        "head_coach": "Justin Langer",
        "owners": ["RPSG Group"],
        "website": "https://www.lucknowsupergiants.in/",
        "twitter": "https://twitter.com/LucknowIPL",
        "instagram": "https://www.instagram.com/lucknowsupergiants/",
        "achievements": ["Playoffs: 2022, 2023"],
        "records": []
    },
]

PLAYERS_SEED = [
    # Only a few exemplar players per team to keep seed light; can be extended later
    {"full_name": "MS Dhoni", "nationality": "India", "role": "Wicketkeeper", "batting_style": "Right-hand bat", "bowling_style": None, "team_slug": "chennai-super-kings", "photo": "https://upload.wikimedia.org/wikipedia/commons/1/18/MS_Dhoni_-_Portrait.jpg", "stats": {"matches": 250, "runs": 5000, "wickets": 0, "strike_rate": 135.0}},
    {"full_name": "Ravindra Jadeja", "nationality": "India", "role": "All-rounder", "batting_style": "Left-hand bat", "bowling_style": "Left-arm orthodox", "team_slug": "chennai-super-kings", "photo": None, "stats": {"matches": 200, "runs": 2700, "wickets": 150}},
    {"full_name": "Rohit Sharma", "nationality": "India", "role": "Batsman", "batting_style": "Right-hand bat", "bowling_style": None, "team_slug": "mumbai-indians", "photo": "https://upload.wikimedia.org/wikipedia/commons/3/30/Rohit_Sharma_in_April_2016_%28cropped%29.jpg", "stats": {"matches": 240, "runs": 6500, "wickets": 15}},
    {"full_name": "Jasprit Bumrah", "nationality": "India", "role": "Bowler", "batting_style": "Right-hand bat", "bowling_style": "Right-arm fast", "team_slug": "mumbai-indians", "stats": {"matches": 130, "runs": 50, "wickets": 160}},
    {"full_name": "Virat Kohli", "nationality": "India", "role": "Batsman", "batting_style": "Right-hand bat", "bowling_style": None, "team_slug": "royal-challengers-bengaluru", "photo": "https://upload.wikimedia.org/wikipedia/commons/7/7e/Virat_Kohli.jpg", "stats": {"matches": 240, "runs": 7500, "wickets": 4}},
    {"full_name": "Faf du Plessis", "nationality": "South Africa", "role": "Batsman", "batting_style": "Right-hand bat", "bowling_style": None, "team_slug": "royal-challengers-bengaluru", "stats": {"matches": 130, "runs": 4200, "wickets": 0}},
    {"full_name": "Sunil Narine", "nationality": "West Indies", "role": "All-rounder", "batting_style": "Right-hand bat", "bowling_style": "Right-arm offbreak", "team_slug": "kolkata-knight-riders", "stats": {"matches": 170, "runs": 1200, "wickets": 170}},
    {"full_name": "Rishabh Pant", "nationality": "India", "role": "Wicketkeeper", "batting_style": "Left-hand bat", "bowling_style": None, "team_slug": "delhi-capitals", "stats": {"matches": 110, "runs": 3000, "wickets": 0}},
    {"full_name": "Sanju Samson", "nationality": "India", "role": "Wicketkeeper", "batting_style": "Right-hand bat", "bowling_style": None, "team_slug": "rajasthan-royals", "stats": {"matches": 150, "runs": 4000, "wickets": 0}},
    {"full_name": "Shubman Gill", "nationality": "India", "role": "Batsman", "batting_style": "Right-hand bat", "bowling_style": None, "team_slug": "gujarat-titans", "stats": {"matches": 90, "runs": 2600}},
    {"full_name": "KL Rahul", "nationality": "India", "role": "Batsman", "batting_style": "Right-hand bat", "bowling_style": None, "team_slug": "lucknow-super-giants", "stats": {"matches": 120, "runs": 4100}},
    {"full_name": "Pat Cummins", "nationality": "Australia", "role": "Bowler", "batting_style": "Right-hand bat", "bowling_style": "Right-arm fast", "team_slug": "sunrisers-hyderabad", "stats": {"matches": 50, "runs": 300, "wickets": 60}},
    {"full_name": "Shikhar Dhawan", "nationality": "India", "role": "Batsman", "batting_style": "Left-hand bat", "bowling_style": None, "team_slug": "punjab-kings", "stats": {"matches": 220, "runs": 6700}},
]

STAFF_SEED = [
    {"full_name": "Stephen Fleming", "role": "Head Coach", "team_slug": "chennai-super-kings"},
    {"full_name": "Mark Boucher", "role": "Head Coach", "team_slug": "mumbai-indians"},
    {"full_name": "Andy Flower", "role": "Head Coach", "team_slug": "royal-challengers-bengaluru"},
]

OWNERS_SEED = [
    {"name": "Chennai Super Kings Cricket Ltd", "company": "CSKCL", "team_slug": "chennai-super-kings", "website": "https://www.chennaisuperkings.com/"},
    {"name": "Indiawin Sports", "team_slug": "mumbai-indians", "website": "https://www.mumbaiindians.com/"},
]


# --------- Startup: ensure indexes + seed if empty ---------
@app.on_event("startup")
def startup_event():
    if db is None:
        return
    db["team"].create_index("slug", unique=True)
    db["player"].create_index([("team_slug", 1), ("full_name", 1)])
    db["staff"].create_index([("team_slug", 1), ("full_name", 1)])
    db["owner"].create_index([("team_slug", 1), ("name", 1)])

    if db["team"].count_documents({}) == 0:
        db["team"].insert_many(TEAMS_SEED)
    if db["player"].count_documents({}) == 0:
        db["player"].insert_many(PLAYERS_SEED)
    if db["staff"].count_documents({}) == 0:
        db["staff"].insert_many(STAFF_SEED)
    if db["owner"].count_documents({}) == 0:
        db["owner"].insert_many(OWNERS_SEED)


# --------- Routes ---------
@app.get("/")
def read_root():
    return {"message": "IPL Encyclopedia Backend is running"}


@app.get("/api/teams")
def list_teams(q: Optional[str] = None):
    filt = {}
    if q:
        filt = {"$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"city": {"$regex": q, "$options": "i"}},
            {"slug": {"$regex": q, "$options": "i"}},
        ]}
    teams = list(db["team"].find(filt))
    return [serialize_doc(t) for t in teams]


@app.get("/api/teams/{slug}")
def get_team(slug: str):
    team = db["team"].find_one({"slug": slug})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    players = list(db["player"].find({"team_slug": slug}))
    staff = list(db["staff"].find({"team_slug": slug}))
    owners = list(db["owner"].find({"team_slug": slug}))

    # group players by role for convenience
    grouped = {"Batsman": [], "Bowler": [], "All-rounder": [], "Wicketkeeper": [], "Other": []}
    for p in players:
        role = p.get("role") or "Other"
        grouped.get(role, grouped["Other"]).append(serialize_doc(p))

    res = serialize_doc(team)
    res["players"] = grouped
    res["staff"] = [serialize_doc(s) for s in staff]
    res["owners"] = [serialize_doc(o) for o in owners]
    return res


@app.get("/api/players")
def list_players(
    team: Optional[str] = Query(None, description="team slug"),
    role: Optional[str] = None,
    nationality: Optional[str] = None,
    q: Optional[str] = None,
):
    filt = {}
    if team:
        filt["team_slug"] = team
    if role:
        filt["role"] = role
    if nationality:
        filt["nationality"] = nationality
    if q:
        filt["$or"] = [
            {"full_name": {"$regex": q, "$options": "i"}},
            {"batting_style": {"$regex": q, "$options": "i"}},
            {"bowling_style": {"$regex": q, "$options": "i"}},
        ]
    docs = list(db["player"].find(filt))
    return [serialize_doc(d) for d in docs]


@app.get("/api/players/{player_id}")
def get_player(player_id: str):
    try:
        doc = db["player"].find_one({"_id": ObjectId(player_id)})
    except Exception:
        doc = None
    if not doc:
        raise HTTPException(status_code=404, detail="Player not found")
    team = db["team"].find_one({"slug": doc.get("team_slug")})
    res = serialize_doc(doc)
    res["team"] = serialize_doc(team) if team else None
    return res


@app.get("/api/staff")
def list_staff(team: Optional[str] = None):
    filt = {"team_slug": team} if team else {}
    docs = list(db["staff"].find(filt))
    return [serialize_doc(d) for d in docs]


@app.get("/api/owners")
def list_owners(team: Optional[str] = None):
    filt = {"team_slug": team} if team else {}
    docs = list(db["owner"].find(filt))
    return [serialize_doc(d) for d in docs]


@app.get("/api/search")
def global_search(q: str = Query(..., min_length=1)):
    regex = {"$regex": q, "$options": "i"}
    teams = [serialize_doc(t) for t in db["team"].find({"$or": [{"name": regex}, {"city": regex}]})]
    players = [serialize_doc(p) for p in db["player"].find({"$or": [{"full_name": regex}, {"nationality": regex}]})]
    owners = [serialize_doc(o) for o in db["owner"].find({"$or": [{"name": regex}, {"company": regex}]})]
    return {"teams": teams, "players": players, "owners": owners}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    # Check env
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
