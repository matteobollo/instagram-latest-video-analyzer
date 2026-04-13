from collections import Counter

from app.models import CommentSentiment, SentimentSummary

POSITIVE_TOKENS = {'bella', 'bello', 'great', 'love', 'amazing', 'bravo', 'top', 'fantastic', 'wow', '🔥', '😍', '❤️'}
NEGATIVE_TOKENS = {'bad', 'terrible', 'hate', 'awful', 'schifo', 'brutto', 'fake', 'worst', '🤮', '😡'}


def classify_text(text: str) -> tuple[str, float]:
    lowered = text.lower()
    positive_hits = sum(token in lowered for token in POSITIVE_TOKENS)
    negative_hits = sum(token in lowered for token in NEGATIVE_TOKENS)

    if positive_hits > negative_hits:
        return 'positive', min(0.55 + positive_hits * 0.15, 0.95)
    if negative_hits > positive_hits:
        return 'negative', min(0.55 + negative_hits * 0.15, 0.95)
    return 'neutral', 0.60 if lowered.strip() else 0.50


def analyze_comments(raw_comments: list[dict]) -> tuple[list[CommentSentiment], SentimentSummary]:
    results: list[CommentSentiment] = []
    counter = Counter()

    for item in raw_comments:
        text = item.get('commentText') or item.get('text') or ''
        label, confidence = classify_text(text)
        counter[label] += 1
        results.append(
            CommentSentiment(
                text=text,
                username=item.get('commentatorUserName') or item.get('ownerUsername'),
                likes_count=item.get('likesCount'),
                sentiment=label,
                confidence=confidence,
            )
        )

    summary = SentimentSummary(
        positive=counter['positive'],
        negative=counter['negative'],
        neutral=counter['neutral'],
        total=len(results),
    )
    return results, summary
