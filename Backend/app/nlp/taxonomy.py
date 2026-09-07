"""Climate policy dimension taxonomy.

Each dimension carries natural-language *prototypes* rather than keywords. The
classifier embeds these prototypes once and scores a chunk by its similarity to
them, so a sentence about "phasing out unabated coal generation by 2035" lands
under Mitigation without the word "mitigation" appearing anywhere -- which the
V1 keyword matcher could not do.

Dimensions follow the reporting structure of the UNFCCC Nationally Determined
Contribution and Biennial Transparency Report guidelines, so the output lines up
with how climate policy is actually assessed.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Dimension:
    key: str
    label: str
    description: str
    prototypes: tuple[str, ...]
    # High-precision lexical cues. Used as a *tie-breaker* that nudges a
    # borderline score, never as the sole basis for a decision.
    cues: tuple[str, ...] = field(default=())


TAXONOMY: tuple[Dimension, ...] = (
    Dimension(
        key="mitigation",
        label="Mitigation Targets",
        description="Commitments to reduce or avoid greenhouse gas emissions.",
        prototypes=(
            "Reduce greenhouse gas emissions by a specified percentage below a base year level.",
            "Achieve net zero emissions or carbon neutrality by a target date.",
            "Phase out unabated coal-fired power generation and fossil fuel subsidies.",
            "Increase the share of renewable energy in the electricity generation mix.",
            "Improve energy efficiency and reduce the carbon intensity of the economy.",
            "Cap emissions through an emissions trading scheme or carbon pricing mechanism.",
            "Capture and destroy methane from landfills, livestock and agricultural sources.",
            "Electrify road transport and shift freight to lower-carbon modes to cut transport emissions.",
            "Expand forests and other carbon sinks so that removals increase.",
            "Peak absolute emissions before a stated date and decline thereafter.",
            "Reduce the carbon intensity of electricity generation.",
            "End routine gas flaring and cut fugitive emissions from fossil fuel production.",
            "Avoid double counting of internationally transferred mitigation outcomes under carbon market cooperation.",
            "Reduce emissions relative to a business-as-usual baseline scenario.",
        ),
        cues=(
            "net zero", "carbon neutral", "emission reduction", "ghg", "co2",
            "decarbonis", "decarboniz", "renewable", "carbon price", "emissions trading",
        ),
    ),
    Dimension(
        key="adaptation",
        label="Adaptation & Resilience",
        description="Measures to reduce vulnerability to climate impacts already locked in.",
        prototypes=(
            "Build resilience of communities and infrastructure to climate change impacts.",
            "Protect coastal zones from sea level rise, storm surge and saline intrusion.",
            "Manage drought, flood and extreme heat risk through early warning systems.",
            "Climate-proof water resources, agriculture and public health systems.",
            "Conduct vulnerability and risk assessments to inform adaptation planning.",
            "Upgrade infrastructure so that it withstands more severe rainfall, flooding or storms.",
            "Secure water supply and storage against longer and more frequent dry seasons.",
            "Screen infrastructure investment for climate risk before approval.",
            "Provide insurance or safety-net instruments against climate-related losses.",
            "Cooperate on river basin management and shared disaster response.",
            "Prepare a national adaptation plan setting out priority actions.",
        ),
        cues=(
            "adaptation", "resilience", "vulnerabilit", "sea level", "flood",
            "drought", "early warning", "climate-proof", "disaster risk",
        ),
    ),
    Dimension(
        key="finance",
        label="Finance & Investment",
        description="Money: budgets, funds, investment needs and financial instruments.",
        prototypes=(
            "Mobilise billions of dollars in climate finance for mitigation and adaptation.",
            "Allocate budget from public funds and attract private sector investment.",
            "Access concessional loans, grants and support from the Green Climate Fund.",
            "Issue green bonds and establish blended finance and de-risking instruments.",
            "Estimate the total investment required to implement the plan.",
            "Set a carbon price, levy or tax rate applying to emitters.",
            "Provide bill support, subsidies or transfers to shield households from energy costs.",
            "Require financial institutions to disclose climate-related risk in their portfolios.",
            "Capitalise a dedicated national climate fund from public revenues.",
            "Use preferential regulatory treatment to expand green lending.",
            "State the annual or total cost of the programme as a share of GDP or in currency terms.",
        ),
        cues=(
            "finance", "funding", "investment", "budget", "billion", "million",
            "green climate fund", "green bond", "grant", "loan", "usd",
        ),
    ),
    Dimension(
        key="governance",
        label="Governance & Legal Framework",
        description="Laws, regulations and the institutions that own delivery.",
        prototypes=(
            "Enact a climate change act establishing legally binding carbon budgets.",
            "Establish a national climate change council or commission to coordinate delivery.",
            "Assign ministerial responsibility and mandate for implementing the strategy.",
            "Introduce regulations, standards and enforcement provisions for compliance.",
            "Integrate climate objectives into national development planning.",
            "Set mandatory standards, codes or performance requirements that regulated parties must meet.",
            "Create an offence, penalty or fine for non-compliance with an obligation.",
            "Establish a statutory committee, regulator or oversight body with defined powers.",
            "Confer powers of inspection, enforcement and administrative sanction on an authority.",
            "Establish a market mechanism or scheme in law, such as an emissions trading system.",
            "Require public procurement and investment appraisal to account for climate objectives.",
            "Devolve or assign implementing responsibilities to subnational authorities.",
        ),
        cues=(
            "act", "law", "regulation", "legislation", "ministry", "council",
            "commission", "authority", "mandate", "governance", "statutory",
        ),
    ),
    Dimension(
        key="mrv",
        label="Monitoring, Reporting & Verification",
        description="How progress is tracked, reported and independently verified.",
        prototypes=(
            "Establish a measurement, reporting and verification system for emissions.",
            "Maintain a national greenhouse gas inventory and report progress biennially.",
            "Define indicators, baselines and milestones to track progress against targets.",
            "Undertake independent review, audit and transparent public reporting.",
            "Require regulated entities above a threshold to report emissions to a national registry.",
            "Require independent third-party verification of reported data.",
            "Publish progress against indicators on a public dashboard or register.",
            "Require disclosure of climate risk exposure.",
        ),
        cues=(
            "mrv", "monitoring", "reporting", "verification", "inventory",
            "indicator", "baseline", "transparency framework", "audit", "review",
        ),
    ),
    Dimension(
        key="sectors",
        label="Sectoral Coverage",
        description="The specific economic sectors the policy acts on.",
        prototypes=(
            "Decarbonise the energy and electricity generation sector.",
            "Reduce emissions from road transport through electric vehicles and public transit.",
            "Address emissions from agriculture, livestock and land use.",
            "Improve waste management, landfill gas capture and the circular economy.",
            "Reduce industrial process emissions in cement, steel and chemicals.",
            "Protect and restore forests, wetlands and other carbon sinks.",
            "Measures targeting the water, drainage and built infrastructure sector.",
            "Coastal and marine infrastructure works within the coastal zone.",
            "Actions in the buildings sector, including construction standards and retrofits.",
            "Actions in the electricity grid and power generation sector.",
            "Actions in the crop and livestock agriculture sector.",
            "Actions in the municipal waste and sanitation sector.",
            "Actions covering aviation, shipping and freight transport.",
            "Actions covering peatlands, wetlands, forestry and other land use.",
        ),
        cues=(
            "energy", "transport", "agricultur", "forestry", "waste", "industr",
            "buildings", "land use", "lulucf", "aviation", "shipping",
        ),
    ),
    Dimension(
        key="equity",
        label="Just Transition & Equity",
        description="Who is affected, who is protected, and how burdens are shared.",
        prototypes=(
            "Ensure a just transition for workers and communities dependent on fossil fuels.",
            "Protect vulnerable, low-income and marginalised groups from climate impacts.",
            "Recognise the rights and knowledge of indigenous peoples and local communities.",
            "Mainstream gender equality and youth participation in climate action.",
            "Address health impacts and energy poverty.",
            "Direct support or protection specifically toward low-income or vulnerable households.",
            "Protect the health of groups most exposed to heat, flooding and disease.",
            "Consult affected workers and unions before closing a facility.",
            "Prioritise elderly people and people with disabilities in emergency response planning.",
            "Monitor energy poverty and distributional fairness as an explicit outcome.",
        ),
        cues=(
            "just transition", "vulnerable", "indigenous", "gender", "equity",
            "poverty", "community", "inclusive", "human rights", "youth",
        ),
    ),
    Dimension(
        key="technology",
        label="Technology & Innovation",
        description="Technology deployment, R&D and capacity building.",
        prototypes=(
            "Deploy carbon capture, utilisation and storage technology at scale.",
            "Invest in green hydrogen, battery storage and grid modernisation.",
            "Support research, development and demonstration of low-carbon technologies.",
            "Facilitate technology transfer and build technical capacity.",
            "Establish a research centre, innovation fund or demonstration programme for low-carbon technology.",
            "Deploy smart grid, demand response and storage technology to integrate variable renewables.",
            "Assess the technical and economic feasibility of an emerging removal technology.",
            "Convert heating systems to heat pumps, waste heat or other low-carbon technology.",
        ),
        cues=(
            "technology", "innovation", "research", "hydrogen", "carbon capture",
            "ccs", "storage", "smart grid", "technology transfer", "capacity building",
        ),
    ),
    Dimension(
        key="international",
        label="International Cooperation",
        description="Engagement with the global climate regime and bilateral partners.",
        prototypes=(
            "Fulfil obligations under the Paris Agreement and the UNFCCC.",
            "Cooperate bilaterally and regionally on climate action and carbon markets.",
            "Use Article 6 cooperative approaches and internationally transferred mitigation outcomes.",
            "Seek international support, including finance, technology and capacity building.",
            "Report to the UNFCCC secretariat under the enhanced transparency framework.",
            "Distinguish the unconditional component of a target from the component conditional on international support.",
            "Respond to the outcome of the global stocktake in setting the level of ambition.",
            "Meet obligations under a multilateral environmental agreement or protocol.",
            "Submit a nationally determined contribution or long-term low-emission development strategy.",
            "Cooperate regionally on shared transboundary environmental risks.",
        ),
        cues=(
            "paris agreement", "unfccc", "article 6", "cop", "bilateral",
            "international cooperation", "ndc", "global stocktake",
        ),
    ),
)

DIMENSIONS_BY_KEY: dict[str, Dimension] = {d.key: d for d in TAXONOMY}
DIMENSION_KEYS: tuple[str, ...] = tuple(d.key for d in TAXONOMY)
