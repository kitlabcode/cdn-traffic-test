from dataclasses import dataclass
from typing import List

@dataclass
class TrafficPhase:
    duration: int
    requests_per_second: int
    payload_size: int    # Removed concurrency

@dataclass
class TrafficScenario:
    name: str
    schedule: List[TrafficPhase]

class TrafficTestFactory:
    BASE_SIZE = 1048576  # 1MB

    @staticmethod
    def create_steady_load_test() -> TrafficScenario:
        """Steady load at 100 MB/s"""
        return TrafficScenario(
            name="steady_load",
            schedule=[
                TrafficPhase(
                    duration=10,
                    requests_per_second=10,  # 100 MB/sec steady
                    payload_size=TrafficTestFactory.BASE_SIZE * 10  # 10MB
                )
            ]
        )

    @staticmethod
    def create_burst_test() -> TrafficScenario:
        """Short burst at 125 MB/s"""
        return TrafficScenario(
            name="burst_test",
            schedule=[
                TrafficPhase(
                    duration=1,
                    requests_per_second=12.5,  # 125 MB/sec peak
                    payload_size=TrafficTestFactory.BASE_SIZE * 10  # 10MB
                )
            ]
        )

    @staticmethod
    def create_spike_pattern() -> TrafficScenario:
        """Pattern with spike to 120 MB/s"""
        return TrafficScenario(
            name="spike_pattern",
            schedule=[
                TrafficPhase(duration=5, requests_per_second=5, payload_size=TrafficTestFactory.BASE_SIZE * 10),    # 50 MB/sec
                TrafficPhase(duration=2, requests_per_second=12, payload_size=TrafficTestFactory.BASE_SIZE * 10),   # 120 MB/sec peak
                TrafficPhase(duration=8, requests_per_second=3, payload_size=TrafficTestFactory.BASE_SIZE * 10)     # 30 MB/sec
            ]
        )

    @staticmethod
    def create_ramp_up_down_test() -> TrafficScenario:
        """Ramp up to 125 MB/s then back down"""
        return TrafficScenario(
            name="ramp_up_down",
            schedule=[
                TrafficPhase(duration=2, requests_per_second=5, payload_size=TrafficTestFactory.BASE_SIZE * 10),    # 50 MB/sec
                TrafficPhase(duration=2, requests_per_second=8, payload_size=TrafficTestFactory.BASE_SIZE * 10),    # 80 MB/sec
                TrafficPhase(duration=2, requests_per_second=12.5, payload_size=TrafficTestFactory.BASE_SIZE * 10), # 125 MB/sec peak
                TrafficPhase(duration=2, requests_per_second=8, payload_size=TrafficTestFactory.BASE_SIZE * 10),    # 80 MB/sec
                TrafficPhase(duration=2, requests_per_second=5, payload_size=TrafficTestFactory.BASE_SIZE * 10)     # 50 MB/sec
            ]
        )

    @staticmethod
    def create_sustained_load_test() -> TrafficScenario:
        return TrafficScenario(
            name="sustained_load",
            schedule=[
                TrafficPhase(duration=300, requests_per_second=8, payload_size=TrafficTestFactory.BASE_SIZE * 10)  # 80 MB/sec
            ]
        )

    @staticmethod
    def create_mixed_payload_test() -> TrafficScenario:
        return TrafficScenario(
            name="mixed_payload_sizes",
            schedule=[
                TrafficPhase(duration=30, requests_per_second=12.5, payload_size=TrafficTestFactory.BASE_SIZE * 10),  # 125 MB/sec
                TrafficPhase(duration=30, requests_per_second=2.5, payload_size=TrafficTestFactory.BASE_SIZE * 50),   # 125 MB/sec
                TrafficPhase(duration=30, requests_per_second=5, payload_size=TrafficTestFactory.BASE_SIZE * 25)      # 125 MB/sec
            ]
        )

    @staticmethod
    def create_oscillating_pattern() -> TrafficScenario:
        return TrafficScenario(
            name="oscillating_load",
            schedule=[
                TrafficPhase(duration=10, requests_per_second=5, payload_size=TrafficTestFactory.BASE_SIZE * 10),   # 50 MB/sec
                TrafficPhase(duration=10, requests_per_second=8, payload_size=TrafficTestFactory.BASE_SIZE * 10),   # 80 MB/sec
                TrafficPhase(duration=10, requests_per_second=5, payload_size=TrafficTestFactory.BASE_SIZE * 10),   # 50 MB/sec
                TrafficPhase(duration=10, requests_per_second=8, payload_size=TrafficTestFactory.BASE_SIZE * 10)    # 80 MB/sec
            ]
        )

    @staticmethod
    def create_stress_test() -> TrafficScenario:
        """
        Stress test pattern:
        - RPS = 12.5 requests/sec
        - Size = 10MB per request
        - Throughput = 125 MB/sec sustained
        """
        return TrafficScenario(
            name="stress_test",
            schedule=[
                TrafficPhase(
                    duration=60,
                    requests_per_second=12.5,    
                    payload_size=TrafficTestFactory.BASE_SIZE * 10  # 10MB
                )
            ]
        )