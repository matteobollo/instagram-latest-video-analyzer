from collections import Counter

from app.models import CommentSentiment, SentimentSummary

POSITIVE_TOKENS = {'bella', 'bello', 'great', 'love', 'amazing', 'bravo', 'top', 'fantastic', 'wow', '🔥', '😍', '❤️', '👏', '🚀', '🔝'}
NEGATIVE_TOKENS = {'bad', 'terrible', 'hate', 'awful', 'schifo', 'brutto', 'fake', 'worst', '🤮', '😡'}


def classify_text(text: str) -> tuple[str, float]:
    """
    Classify a comment text as positive, negative or neutral.

    :param text: The comment text to classify.
    :return: A tuple containing the label and the confidence.
    """
    lowered = text.lower()
    positive_hits = sum(token in lowered for token in POSITIVE_TOKENS)
    negative_hits = sum(token in lowered for token in NEGATIVE_TOKENS)

    # If there are more positive hits than negative hits, classify as positive.
    # If there are more negative hits than positive hits, classify as negative.
    # Otherwise, classify as neutral.
    if positive_hits > negative_hits:
        confidence = min(0.55 + positive_hits * 0.15, 0.95)
        return 'positive', confidence
    if negative_hits > positive_hits:
        confidence = min(0.55 + negative_hits * 0.15, 0.95)
        return 'negative', confidence
    # If the text is not empty, classify as neutral with a medium confidence.
    # If the text is empty, classify as neutral with a low confidence.
    if lowered.strip():
        return 'neutral', 0.60
    return 'neutral', 0.50


def analyze_comments(raw_comments: list[dict]) -> tuple[list[CommentSentiment], SentimentSummary]:
    """
    Analyze a list of comments, classify each comment as positive, negative or neutral,
    and return a tuple containing a list of CommentSentiment objects and a SentimentSummary object.

    :param raw_comments: A list of comments to analyze.
    :return: A tuple containing a list of CommentSentiment objects and a SentimentSummary object.
    """
    results: list[CommentSentiment] = []
    counter = Counter()

    # Iterate over each comment and classify it as positive, negative or neutral.
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

    # Create a SentimentSummary object with the counters.
    summary = SentimentSummary(
        positive=counter['positive'],
        negative=counter['negative'],
        neutral=counter['neutral'],
        total=len(results),
    )
    return results, summary
