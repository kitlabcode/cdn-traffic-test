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
    MAX_RPS = 50  # Cap maximum requests per second

    @staticmethod
    def create_steady_load_test() -> TrafficScenario:
        """Steady load at 25 MB/s"""
        return TrafficScenario(
            name="steady_load",
            schedule=[
                TrafficPhase(
                    duration=10,
                    requests_per_second=25,  # 25 MB/sec
                    payload_size=TrafficTestFactory.BASE_SIZE
                )
            ]
        )

    @staticmethod
    def create_burst_test() -> TrafficScenario:
        """Short burst at 40 MB/s"""
        return TrafficScenario(
            name="burst_test",
            schedule=[
                TrafficPhase(
                    duration=1,
                    requests_per_second=40,  # 40 MB/sec
                    payload_size=TrafficTestFactory.BASE_SIZE
                )
            ]
        )

    @staticmethod
    def create_spike_pattern() -> TrafficScenario:
        """Pattern with spike to 35 MB/s"""
        return TrafficScenario(
            name="spike_pattern",
            schedule=[
                TrafficPhase(duration=5, requests_per_second=15, payload_size=TrafficTestFactory.BASE_SIZE),    # 15 MB/sec
                TrafficPhase(duration=2, requests_per_second=35, payload_size=TrafficTestFactory.BASE_SIZE),    # 35 MB/sec peak
                TrafficPhase(duration=8, requests_per_second=10, payload_size=TrafficTestFactory.BASE_SIZE)     # 10 MB/sec
            ]
        )

    @staticmethod
    def create_ramp_up_down_test() -> TrafficScenario:
        """Ramp up to 35 MB/s then back down"""
        return TrafficScenario(
            name="ramp_up_down",
            schedule=[
                TrafficPhase(duration=2, requests_per_second=15, payload_size=TrafficTestFactory.BASE_SIZE),    # 15 MB/sec
                TrafficPhase(duration=2, requests_per_second=25, payload_size=TrafficTestFactory.BASE_SIZE),    # 25 MB/sec
                TrafficPhase(duration=2, requests_per_second=35, payload_size=TrafficTestFactory.BASE_SIZE),    # 35 MB/sec peak
                TrafficPhase(duration=2, requests_per_second=25, payload_size=TrafficTestFactory.BASE_SIZE),    # 25 MB/sec
                TrafficPhase(duration=2, requests_per_second=15, payload_size=TrafficTestFactory.BASE_SIZE)     # 15 MB/sec
            ]
        )

    @staticmethod
    def create_sustained_load_test() -> TrafficScenario:
        return TrafficScenario(
            name="sustained_load",
            schedule=[
                TrafficPhase(duration=300, requests_per_second=25, payload_size=TrafficTestFactory.BASE_SIZE)  # 25 MB/sec
            ]
        )

    @staticmethod
    def create_mixed_payload_test() -> TrafficScenario:
        return TrafficScenario(
            name="mixed_payload_sizes",
            schedule=[
                TrafficPhase(duration=30, requests_per_second=35, payload_size=TrafficTestFactory.BASE_SIZE),  # 35 MB/sec
                TrafficPhase(duration=30, requests_per_second=7, payload_size=TrafficTestFactory.BASE_SIZE * 5),   # 35 MB/sec
                TrafficPhase(duration=30, requests_per_second=14, payload_size=TrafficTestFactory.BASE_SIZE * 2.5)  # 35 MB/sec
            ]
        )

    @staticmethod
    def create_oscillating_pattern() -> TrafficScenario:
        return TrafficScenario(
            name="oscillating_load",
            schedule=[
                TrafficPhase(duration=10, requests_per_second=15, payload_size=TrafficTestFactory.BASE_SIZE),   # 15 MB/sec
                TrafficPhase(duration=10, requests_per_second=25, payload_size=TrafficTestFactory.BASE_SIZE),   # 25 MB/sec
                TrafficPhase(duration=10, requests_per_second=15, payload_size=TrafficTestFactory.BASE_SIZE),   # 15 MB/sec
                TrafficPhase(duration=10, requests_per_second=25, payload_size=TrafficTestFactory.BASE_SIZE)    # 25 MB/sec
            ]
        )

    @staticmethod
    def create_stress_test() -> TrafficScenario:
        """
        Stress test pattern:
        - RPS = 30 requests/sec
        - Size = 1MB per request
        - Throughput = 30 MB/sec sustained
        """
        return TrafficScenario(
            name="stress_test",
            schedule=[
                TrafficPhase(
                    duration=60,
                    requests_per_second=30,    # 30 MB/sec
                    payload_size=TrafficTestFactory.BASE_SIZE
                )
            ]
        )