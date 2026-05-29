from datetime import datetime

from pydantic import BaseModel


class ProfileStatsRead(BaseModel):
    booksRead: int
    pagesRead: int
    avgRating: float
    reviewsWritten: int
    readingStreak: int


class ReadingActivityRead(BaseModel):
    date: datetime
    action: str
    title: str
