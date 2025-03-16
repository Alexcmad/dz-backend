from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import event
from sqlalchemy.orm import Session
from . import models, ai
import numpy as np


class HybridCorrelator:
    def __init__(self, 
                 max_distance_km: float = 5.0,
                 max_time_hours: int = 24,
                 min_tag_similarity: float = 0.3,
                 weights: dict = None):
        self.max_distance = max_distance_km
        self.max_time_window = timedelta(hours=max_time_hours)
        self.min_tag_similarity = min_tag_similarity
        self.weights = weights or {
            'location': 0.4,
            'tags': 0.3,
            'time': 0.3
        }

    def calculate_location_similarity(self, lat1: float, lon1: float, 
                                   lat2: float, lon2: float) -> float:
        """Calculate location similarity score based on Haversine distance."""
        R = 6371  # Earth's radius in kilometers

        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        distance = R * c

        # Convert distance to similarity score (0-1)
        similarity = max(0, 1 - (distance / self.max_distance))
        return similarity

    def calculate_tag_similarity(self, tags1: List[str], tags2: List[str]) -> float:
        """Calculate tag similarity using Jaccard similarity."""
        set1, set2 = set(tags1), set(tags2)
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union

    def calculate_time_similarity(self, time1: datetime, time2: datetime) -> float:
        """Calculate time similarity based on time difference."""
        time_diff = abs(time1 - time2)
        if time_diff > self.max_time_window:
            return 0.0
        
        # Convert time difference to similarity score (1.0 to 0.0)
        # Using exponential decay to give higher weight to more recent events
        hours_diff = time_diff.total_seconds() / 3600
        similarity = np.exp(-hours_diff / (self.max_time_window.total_seconds() / 3600))
        return similarity

    def get_correlation_score(self, report1: models.Report, report2: models.Report) -> float:
        """Calculate overall correlation score between two reports."""
        # Location similarity
        location_similarity = self.calculate_location_similarity(
            report1.location.latitude, report1.location.longitude,
            report2.location.latitude, report2.location.longitude
        )

        # Tag similarity
        tag_similarity = self.calculate_tag_similarity(report1.tags, report2.tags)

        # Time similarity
        time_similarity = self.calculate_time_similarity(
            report1.created_at, report2.created_at
        )

        # Calculate weighted score
        score = (
            location_similarity * self.weights['location'] +
            tag_similarity * self.weights['tags'] +
            time_similarity * self.weights['time']
        )

        return score


class EventCorrelationService:
    def __init__(self, correlation_threshold: float = 0.6):
        self.correlator = HybridCorrelator()
        self.threshold = correlation_threshold

    def find_matching_event(self, db: Session, report: models.Report) -> Optional[models.Event]:
        """Find the best matching event for a report."""
        # Get recent events within time window
        time_threshold = datetime.utcnow() - self.correlator.max_time_window
        
        # Get all events with their most recent reports
        recent_events = (
            db.query(models.Event)
            .select_from(models.Event)
            .join(models.event_reports)
            .join(models.Report)
            .filter(models.Report.created_at >= time_threshold)
            .distinct()
            .all()
        )

        best_match = None
        highest_score = 0

        for event in recent_events:
            # Get the most recent report from this event
            latest_report = (
                db.query(models.Report)
                .join(models.event_reports)
                .filter(models.event_reports.c.event_id == event.id)
                .order_by(models.Report.created_at.desc())
                .first()
            )
            
            if latest_report:
                score = self.correlator.get_correlation_score(report, latest_report)
                
                if score > highest_score and score >= self.threshold:
                    highest_score = score
                    best_match = event

        return best_match

    def create_or_update_event(self, db: Session, report: models.Report) -> models.Event:
        """Create a new event or update existing one based on the report."""
        matching_event = self.find_matching_event(db, report)

        if matching_event:
            # Update existing event
            matching_event.reports.append(report)
            
            # Create a summary of the event for AI description generation
            event_summary = f"Location: {matching_event.location.name}\n"
            event_summary += f"Time: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            event_summary += f"Tags: {', '.join(matching_event.tags)}\n"
            event_summary += "Reports:\n"
            for r in matching_event.reports:
                event_summary += f"- {r.content} (Severity: {r.severity}, Time: {r.created_at.strftime('%Y-%m-%d %H:%M:%S')})\n"
            
            # Generate new description
            matching_event.description = ai.generate_event_description(event_summary)
            
            # Update tags if new ones are present
            matching_event.tags = list(set(matching_event.tags + report.tags))
            db.commit()
            return matching_event
        else:
            # Create new event
            new_event = models.Event(
                description=report.content,
                tags=report.tags,
                location_id=report.location_id,
                reports=[report]
            )
            
            # Create initial summary for AI description
            event_summary = f"Location: {report.location.name}\n"
            event_summary += f"Time: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            event_summary += f"Tags: {', '.join(report.tags)}\n"
            event_summary += f"Initial Report: {report.content} (Severity: {report.severity})\n"
            
            # Generate initial description
            new_event.description = ai.generate_event_description(event_summary)
            
            db.add(new_event)
            db.commit()
            db.refresh(new_event)
            return new_event 