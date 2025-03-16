from sqlalchemy.orm import Session
from . import models
from typing import List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .correlation import EventCorrelationService

# Initialize the correlation service with default settings
correlation_service = EventCorrelationService(
    correlation_threshold=0.6  # Adjust this threshold based on testing
)


def get_text_similarity(text1: str, text2: str) -> float:
    """Calculate text similarity between two descriptions using TF-IDF and cosine similarity."""
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]


def calculate_location_proximity(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the proximity score between two locations using Haversine distance."""
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    distance = R * c

    # Convert distance to a proximity score (0-1)
    # We'll consider locations within 5km as very similar (score > 0.8)
    proximity = 1 / (1 + distance/5)
    return proximity


def find_matching_event(db: Session, report: models.Report, similarity_threshold: float = 0.7) -> models.Event | None:
    """Find a matching event for a given report based on description and location similarity."""
    events = db.query(models.Event).filter(
        models.Event.location_id == report.location_id
    ).all()

    best_match = None
    highest_similarity = 0

    for event in events:
        # Calculate text similarity
        text_similarity = get_text_similarity(report.content, event.description)
        
        # Calculate tag similarity
        common_tags = set(report.tags) & set(event.tags)
        tag_similarity = len(common_tags) / max(len(report.tags), len(event.tags)) if report.tags and event.tags else 0

        # Calculate location proximity
        report_location = report.location
        event_location = event.location
        location_proximity = calculate_location_proximity(
            report_location.latitude, report_location.longitude,
            event_location.latitude, event_location.longitude
        )

        # Calculate overall similarity
        overall_similarity = (text_similarity * 0.4 + tag_similarity * 0.3 + location_proximity * 0.3)

        if overall_similarity > highest_similarity:
            highest_similarity = overall_similarity
            best_match = event

    return best_match if highest_similarity >= similarity_threshold else None


def create_or_update_event(db: Session, report: models.Report) -> models.Event:
    """Create a new event or update existing one based on the report."""
    return correlation_service.create_or_update_event(db, report) 