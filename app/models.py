import uuid
from sqlalchemy import Column, Integer, Float, String, Text
from sqlalchemy.orm import declarative_base  # Updated for SQLAlchemy 2.0+
import json

Base = declarative_base()

class TrafficTestResultModel(Base):
    __tablename__ = 'traffic_test_results'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))  # Use STRING for UUID
    pattern = Column(String, nullable=False)
    p50 = Column(Float, nullable=False)
    p95 = Column(Float, nullable=False)
    p99 = Column(Float, nullable=False)
    p999 = Column(Float, nullable=False)
    success_rate = Column(Float, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    std_dev = Column(Float, nullable=False)
    successful_requests = Column(Integer, nullable=False)
    total_requests = Column(Integer, nullable=False)
    status_code_counts = Column(Text, nullable=False)  # Store JSON as TEXT
    error_counts = Column(Text, nullable=False)  # Store JSON as TEXT

    def set_status_code_counts(self, counts):
        self.status_code_counts = json.dumps(counts)

    def get_status_code_counts(self):
        return json.loads(self.status_code_counts)

    def set_error_counts(self, counts):
        self.error_counts = json.dumps(counts)

    def get_error_counts(self):
        return json.loads(self.error_counts)

    def __repr__(self):
        return f"<TrafficTestResult(pattern='{self.pattern}', p50={self.p50}, p95={self.p95}, p99={self.p99}, p999={self.p999}, success_rate={self.success_rate})>"