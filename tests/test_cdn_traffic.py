import pytest
import requests
import time
import concurrent.futures
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import TrafficTestResultModel, Base
from datetime import datetime
import os
from collections import defaultdict
import json
import logging

# CrateDB setup
DATABASE_URL = f"crate://cratedb:4200"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Ensure the database schema is created
Base.metadata.create_all(engine)

# HOSTNAME setup
HOSTNAME = os.getenv("HOSTNAME", "localhost")

# Logging setup
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler("cdn_traffic_test.log", mode="a")  # Log to a file
    ]
)

def load_traffic_scenarios(filepath="traffic_scenarios.json"):
    """Loads traffic scenarios from a JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Error: File not found at {filepath}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Error: Could not decode JSON in {filepath}: {e}")
        return []

def execute_traffic_phase(url, duration, requests_per_second, concurrency, payload_size):
    response_times = []
    status_codes = defaultdict(int)
    error_counts = defaultdict(int)
    successful_requests = 0
    interval = 1 / requests_per_second if requests_per_second > 0 else 1
    num_requests = int(duration * requests_per_second) if requests_per_second > 0 else 0

    def send_request():
        nonlocal successful_requests
        try:
            response = requests.get(url)
            response_times.append(response.elapsed.microseconds / 1000)
            status_codes[response.status_code] += 1  # Increment status code count
            if response.status_code == 200:
                successful_requests += 1
            return response.status_code
        except requests.exceptions.RequestException as e:
            error_counts["Request Error"] += 1
            return None

    if num_requests > 0:
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = []
            for _ in range(num_requests):
                futures.append(executor.submit(send_request))
                time.sleep(interval)
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
    return response_times, status_codes, error_counts, successful_requests

@pytest.mark.parametrize("traffic_scenario", load_traffic_scenarios())
def test_cdn_traffic(traffic_scenario):
    scenario_name = traffic_scenario.get("name", "generic_scenario")
    all_response_times = []
    all_status_codes = defaultdict(int)
    all_error_counts = defaultdict(int)
    total_successful_requests = 0
    start_time = datetime.now()

    # Calculate total_requests before the assertion
    total_requests = sum(
        phase.get("duration", 1) * phase.get("requests_per_second", 1)
        for phase in traffic_scenario.get("schedule", [])
    )

    for phase in traffic_scenario.get("schedule", []):
        duration = phase.get("duration", 1)
        requests_per_second = phase.get("requests_per_second", 1)
        concurrency = phase.get("concurrency", 1)
        payload_size = phase.get("payload_size", 1)
        url = f"http://{HOSTNAME}/cache/{payload_size}/{scenario_name.lower().replace(' ', '_')}_phase"

        response_times, status_codes, error_counts, successful_requests = execute_traffic_phase(
            url, duration, requests_per_second, concurrency, payload_size
        )
        all_response_times.extend(response_times)
        for code, count in status_codes.items():
            all_status_codes[code] += count
        for error, count in error_counts.items():
            all_error_counts[error] += count
        total_successful_requests += successful_requests
        time.sleep(0.1)  # Small pause between phases

    end_time = datetime.now()

    # Perform assertions and save results
    assert all_status_codes.get(200, 0) == total_requests, f"Some requests failed: {all_status_codes}, Errors: {all_error_counts}"

    # Calculate and log metrics
    if all_response_times:
        all_response_times.sort()
        p50 = np.percentile(all_response_times, 50)
        p95 = np.percentile(all_response_times, 95)
        p99 = np.percentile(all_response_times, 99)
        p999 = np.percentile(all_response_times, 99.9)
        std_dev = np.std(all_response_times)
    else:
        p50 = p95 = p99 = p999 = std_dev = 0

    success_rate = (total_successful_requests / total_requests) * 100 if total_requests > 0 else 0

    logging.info(f"\n--- {scenario_name.capitalize()} Traffic Test Results ---")
    logging.info(f"Total Requests (approximate): {total_requests}")
    logging.info(f"Response Time Percentiles (ms): p50={p50:.2f}, p95={p95:.2f}, p99={p99:.2f}, p999={p999:.2f}")
    logging.info(f"Response Time Standard Deviation (ms): {std_dev:.2f}")
    logging.info(f"Success Rate: {success_rate:.2f}%")
    logging.info("Status Code Distribution: %s", dict(all_status_codes))
    if all_error_counts:
        logging.info("Error Counts: %s", dict(all_error_counts))
    logging.info(f"Start Time: {start_time}, End Time: {end_time}")

    # Save results to CrateDB
    result = TrafficTestResultModel(
        pattern=scenario_name,
        p50=p50,
        p95=p95,
        p99=p99,
        p999=p999,
        success_rate=success_rate,
        start_time=start_time,
        end_time=end_time,
        std_dev=std_dev,
        successful_requests=total_successful_requests,
        total_requests=total_requests,
    )
    result.set_status_code_counts(dict(all_status_codes))
    result.set_error_counts(dict(all_error_counts))
    try:
        session.add(result)
        session.commit()
    except Exception as e:
        logging.error(e)
        session.rollback()