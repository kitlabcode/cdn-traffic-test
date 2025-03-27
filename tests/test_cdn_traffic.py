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
from app.traffic_test_factory import TrafficTestFactory
import math

# CrateDB setup
DATABASE_URL = os.getenv("DATABASE_URL", "crate://localhost:4200")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Ensure the database schema is created
Base.metadata.create_all(engine)

# HOSTNAME setup
target_hostname = os.getenv("TARGET_HOSTNAME", "localhost")

# Logging setup
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler("cdn_traffic_test.log", mode="a")  # Log to a file
    ]
)

def execute_traffic_phase(url, duration, requests_per_second):
    response_times = []
    status_codes = defaultdict(int)
    error_counts = defaultdict(int)
    successful_requests = 0
    interval = 1 / requests_per_second if requests_per_second > 0 else 1
    num_requests = int(duration * requests_per_second) if requests_per_second > 0 else 0

    def send_request():
        nonlocal successful_requests
        try:
            response = requests.get(url, timeout=(3.05, 27))
            response_times.append(response.elapsed.microseconds / 1000)
            status_codes[response.status_code] += 1
            if response.status_code == 200:
                successful_requests += 1
            return response.status_code
        except requests.exceptions.Timeout as e:
            logging.warning(f"Request timed out: {e}")
            error_counts["Timeout Error"] += 1
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error: {e}")
            error_counts["Request Error"] += 1
            return None

    if num_requests > 0:
        with concurrent.futures.ThreadPoolExecutor() as executor:  # Let Python manage pool size
            futures = []
            start_time = time.time()
            
            # Submit all requests at their scheduled times
            for i in range(num_requests):
                target_time = start_time + (i * interval)
                now = time.time()
                if now < target_time:
                    time.sleep(target_time - now)
                futures.append(executor.submit(send_request))

            # Wait for completion
            try:
                done, not_done = concurrent.futures.wait(
                    futures,
                    timeout=duration + 30,  # Allow extra time for completion
                    return_when=concurrent.futures.ALL_COMPLETED
                )
                
                for future in done:
                    try:
                        future.result(timeout=1)
                    except Exception as e:
                        logging.error(f"Request failed: {e}")
                        error_counts["Execution Error"] += 1

                if not_done:
                    logging.error(f"{len(not_done)} requests did not complete")
                    error_counts["Incomplete Requests"] += len(not_done)
                    for future in not_done:
                        future.cancel()
                        
            except concurrent.futures.TimeoutError:
                logging.error("Batch execution timed out")
                error_counts["Batch Timeout"] += 1
                for future in futures:
                    future.cancel()

    return response_times, status_codes, error_counts, successful_requests

def collect_results(futures):
    results = []
    for future in concurrent.futures.as_completed(futures):
        try:
            results.append(future.result())
        except Exception as e:
            logging.error(f"Request failed: {e}")
    return results

def get_test_scenarios():
    factory = TrafficTestFactory()
    scenarios = [
        factory.create_steady_load_test(),
        factory.create_burst_test(),
        factory.create_spike_pattern(),
        factory.create_ramp_up_down_test(),
        factory.create_sustained_load_test(),
        factory.create_mixed_payload_test(),
        factory.create_oscillating_pattern(),
        factory.create_stress_test()
    ]
    # Return tuple of (name, scenario) for better test identification
    return [(scenario.name, scenario) for scenario in scenarios]

@pytest.mark.parametrize("scenario_name,traffic_scenario", get_test_scenarios())
def test_cdn_traffic(scenario_name, traffic_scenario):
    all_response_times = []
    all_status_codes = defaultdict(int)
    all_error_counts = defaultdict(int)
    total_successful_requests = 0
    start_time = datetime.now()

    # Calculate total_requests using ceil to round up fractional requests
    total_requests = sum(
        math.ceil(phase.duration * phase.requests_per_second)
        for phase in traffic_scenario.schedule
    )

    for phase in traffic_scenario.schedule:
        url = f"http://{target_hostname}/cache/{phase.payload_size}/{scenario_name.lower().replace(' ', '_')}_phase"
        logging.info(f"Starting phase with {phase.requests_per_second} RPS for {phase.duration}s")
        
        response_times, status_codes, error_counts, successful_requests = execute_traffic_phase(
            url, 
            phase.duration, 
            phase.requests_per_second, 
        )
        
        # Aggregate results
        all_response_times.extend(response_times)
        for code, count in status_codes.items():
            all_status_codes[code] += count
        for error, count in error_counts.items():
            all_error_counts[error] += count
        total_successful_requests += successful_requests
        
        logging.info(f"Completed phase: {successful_requests}/{phase.duration * phase.requests_per_second} successful requests")

    end_time = datetime.now()

    # Update assertion to allow for fractional RPS
    min_acceptable_requests = sum(
        math.floor(phase.duration * phase.requests_per_second)
        for phase in traffic_scenario.schedule
    )
    
    assert all_status_codes.get(200, 0) >= min_acceptable_requests, \
        f"Too few successful requests. Got: {all_status_codes.get(200, 0)}, " \
        f"Expected at least: {min_acceptable_requests}. " \
        f"Status codes: {dict(all_status_codes)}, Errors: {dict(all_error_counts)}"

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