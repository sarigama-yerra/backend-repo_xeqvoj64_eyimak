"""
Database Schemas for IPL Encyclopedia

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- Team -> "team"
- Player -> "player"
- Staff -> "staff"
- Owner -> "owner"
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional

class Owner(BaseModel):
    name: str
    company: Optional[str] = None
    logo: Optional[HttpUrl] = None
    description: Optional[str] = None
    team_slug: Optional[str] = Field(None, description="Slug of the team they own")
    website: Optional[HttpUrl] = None
    twitter: Optional[HttpUrl] = None
    instagram: Optional[HttpUrl] = None

class Staff(BaseModel):
    full_name: str
    role: str = Field(..., description="e.g., Head Coach, Bowling Coach, Mentor, Physio")
    photo: Optional[HttpUrl] = None
    team_slug: str

class Player(BaseModel):
    full_name: str
    nationality: str
    role: str = Field(..., description="Batsman, Bowler, All-rounder, Wicketkeeper")
    batting_style: Optional[str] = None
    bowling_style: Optional[str] = None
    photo: Optional[HttpUrl] = None
    team_slug: str
    stats: Optional[dict] = Field(default_factory=dict, description="IPL stats like matches, runs, wickets, strike_rate, economy, average")

class Team(BaseModel):
    name: str
    slug: str = Field(..., description="URL-friendly unique identifier, e.g., chennai-super-kings")
    short_name: Optional[str] = None
    logo: Optional[HttpUrl] = None
    colors: List[str] = Field(default_factory=list)
    home_ground: Optional[str] = None
    city: Optional[str] = None
    captain: Optional[str] = None
    head_coach: Optional[str] = None
    owners: List[str] = Field(default_factory=list, description="Owner names")
    website: Optional[HttpUrl] = None
    twitter: Optional[HttpUrl] = None
    instagram: Optional[HttpUrl] = None
    achievements: List[str] = Field(default_factory=list)
    records: List[str] = Field(default_factory=list)
