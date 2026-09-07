"""Shared fixtures.

Every test runs against a temporary data directory, so the suite never touches
a developer's real document library and tests cannot leak state into each other.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Must be set before app.config is imported anywhere.
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("ANTHROPIC_API_KEY", "")


@pytest.fixture(scope="session", autouse=True)
def isolated_data_dir(tmp_path_factory):
    from app.config import get_settings

    data_dir = tmp_path_factory.mktemp("policy-data")
    get_settings.cache_clear()
    os.environ["DATA_DIR"] = str(data_dir)

    settings = get_settings()
    from app.store import repository as repo

    repo.init_db()
    yield settings

    get_settings.cache_clear()


TEST_PASSWORD = "correct-horse-battery-staple"


@pytest.fixture
def policy_a_text() -> str:
    return POLICY_A


@pytest.fixture
def policy_b_text() -> str:
    return POLICY_B


POLICY_A = """NATIONAL CLIMATE CHANGE POLICY 2024

1. INTRODUCTION

This policy sets out the national response to climate change for the period to
2035. It is issued under the Climate Change Act 2023.

2. MITIGATION TARGETS

The country will reduce greenhouse gas emissions by 45% below 2005 levels by
2030. The Government commits to achieving net zero emissions by 2050. Renewable
energy will account for 70% of national electricity generation by 2030, up from
35% in 2020. Fossil fuel subsidies will be phased out by 2027.

3. ADAPTATION AND RESILIENCE

Coastal protection works will be constructed along 120 km of shoreline to defend
communities against sea level rise and storm surge. A national multi-hazard early
warning system will be established. Climate-resilient crop varieties will be
distributed to smallholder farmers in drought-prone districts.

4. FINANCE

The total investment required to deliver the mitigation component is estimated at
USD 12.6 billion over the period to 2030. The Government will issue sovereign
green bonds. An annual budget allocation of USD 400 million is committed to the
adaptation programme.

5. MONITORING AND REPORTING

A measurement, reporting and verification system will be established to track
emissions across all covered sectors. The national greenhouse gas inventory will
be updated annually and progress reported biennially.

6. INTERNATIONAL COOPERATION

This contribution is submitted in accordance with Article 4 of the Paris
Agreement. Technology transfer arrangements will be sought from development
partners.
"""

POLICY_B = """CLIMATE ACTION STRATEGY 2025-2040

A. PURPOSE

This strategy describes the actions the Government will take to address climate
change through 2040.

B. EMISSIONS REDUCTION

We will cut emissions by 30% compared to 2010 by 2035. Carbon neutrality is
targeted by 2060. Solar and wind capacity will reach 5000 MW by 2032. An
emissions trading scheme covering power generation and heavy industry will
commence operation in 2028.

C. SECTORS

Emissions from road transport will be reduced through electrification of the
public bus fleet. Methane emissions from paddy cultivation and livestock will be
addressed through improved water management. Forest cover will be increased to
32% of land area.

D. JUST TRANSITION

A just transition programme will provide retraining and income support to workers
displaced from coal-dependent industries. Gender-responsive budgeting will be
applied so that women and youth benefit equitably. The rights of indigenous and
local communities will be respected in all land-based measures.

E. TECHNOLOGY

Green hydrogen production and grid-scale battery storage will be supported
through targeted research and development funding. Carbon capture, utilisation
and storage will be demonstrated at two industrial sites by 2032.
"""


def register_and_authenticate(client, email: str = "tester@example.com") -> dict:
    """Create a user and return the headers that authenticate them.

    Every API test runs as a real authenticated user, which means the tests
    exercise the same authorisation path as production rather than a bypass.
    """
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": TEST_PASSWORD, "display_name": "Tester"},
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
