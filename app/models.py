from typing import Literal
from pydantic import BaseModel, Field


SentimentLabel = Literal["positive", "negative", "neutral"]


class CommentSentiment(BaseModel):
    text: str
    username: str | None = None
    likes_count: int | None = None
    sentiment: SentimentLabel
    confidence: float = Field(ge=0.0, le=1.0)


class SentimentSummary(BaseModel):
    positive: int
    negative: int
    neutral: int
    total: int


class TranscriptResult(BaseModel):
    voice_detected: bool
    transcript: str | None = None
    language: str | None = None


class VideoAnalysis(BaseModel):
    duration_seconds: float | None = None
    bpm: float | None = None
    bpm_detected: bool = False
    transcript: TranscriptResult


class PostMetadata(BaseModel):
    post_url: str
    shortcode: str | None = None
    caption: str | None = None
    owner_username: str
    timestamp: str | None = None
    comments_count: int | None = None
    likes_count: int | None = None
    video_url: str | None = None
    downloaded_video_url: str | None = None


class AnalyzeResponse(BaseModel):
    handle: str
    source: str = "instagram"
    status: str = "ok"
    post: PostMetadata
    comments: list[CommentSentiment]
    sentiment_summary: SentimentSummary
    video_analysis: VideoAnalysis
