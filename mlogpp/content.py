from .value_types import Type


class Content:
    BLOCKS: set[str] = {
        "graphite-press", "multi-press", "silicon-smelter", "silicon-crucible", "kiln", "plastanium-compressor",
        "phase-weaver", "cryofluid-mixer", "pyratite-mixer", "blast-mixer", "melter", "separator", "disassembler",
        "spore-press", "pulverizer", "coal-centrifuge", "incinerator", "copper-wall", "copper-wall-large",
        "titanium-wall", "titanium-wall-large", "plastanium-wall", "plastanium-wall-large", "thorium-wall",
        "thorium-wall-large", "phase-wall", "phase-wall-large", "surge-wall", "surge-wall-large", "door", "door-large",
        "scrap-wall", "scrap-wall-large", "scrap-wall-huge", "scrap-wall-gigantic", "mender", "mend-projector",
        "overdrive-projector", "overdrive-dome", "force-projector", "shock-mine", "conveyor", "titanium-conveyor",
        "plastanium-conveyor", "armored-conveyor", "junction", "bridge-conveyor", "phase-conveyor", "sorter",
        "inverted-sorter", "router", "distributor", "overflow-gate", "underflow-gate", "mass-driver", "duct",
        "duct-router", "duct-bridge", "mechanical-pump", "rotary-pump", "conduit", "pulse-conduit", "plated-conduit",
        "liquid-router", "liquid-tank", "liquid-junction", "bridge-conduit", "phase-conduit", "power-node",
        "power-node-large", "surge-tower", "diode", "battery", "battery-large", "combustion-generator",
        "thermal-generator", "steam-generator", "differential-generator", "rtg-generator", "solar-panel",
        "solar-panel-large", "thorium-reactor", "impact-reactor", "mechanical-drill", "pneumatic-drill", "laser-drill",
        "blast-drill", "water-extractor", "cultivator", "oil-extractor", "core-shard", "core-foundation",
        "core-nucleus", "vault", "container", "unloader", "duo", "scatter", "scorch", "hail", "wave", "lancer", "arc",
        "parallax", "swarmer", "salvo", "segment", "tsunami", "fuse", "ripple", "cyclone", "foreshadow", "spectre",
        "meltdown", "command-center", "ground-factory", "air-factory", "naval-factory", "additive-reconstructor",
        "multiplicative-reconstructor", "exponential-reconstructor", "tetrative-reconstructor", "repair-point",
        "repair-turret", "payload-conveyor", "payload-router", "payload-propulsion-tower", "power-source", "power-void",
        "item-source", "item-void", "liquid-source", "liquid-void", "payload-void", "payload-source", "illuminator",
        "launch-pad", "interplanetary-accelerator", "message", "switch", "micro-processor", "logic-processor",
        "hyper-processor", "memory-cell", "memory-bank", "logic-display", "large-logic-display", "liquid-container",
        "deconstructor", "constructor", "thruster", "large-constructor", "payload-loader", "payload-unloader",
        "silicon-arc-furnace", "cliff-crusher", "plasma-bore", "reinforced-liquid-junction", "breach", "core-bastion",
        "turbine-condenser", "beam-node", "beam-tower", "build-tower", "impact-drill", "carbide-crucible",
        "surge-conveyor", "duct-unloader", "surge-router", "reinforced-conduit", "reinforced-liquid-router",
        "reinforced-liquid-container", "reinforced-liquid-tank", "reinforced-bridge-conduit", "core-citadel",
        "core-acropolis", "heat-reactor", "impulse-pump", "reinforced-pump", "electrolyzer", "oxidation-chamber",
        "surge-smelter", "surge-crucible", "overflow-duct", "large-plasma-bore", "cyanogen-synthesizer",
        "slag-centrifuge", "electric-heater", "slag-incinerator", "phase-synthesizer", "sublimate",
        "reinforced-container", "reinforced-vault", "atmospheric-concentrator", "unit-cargo-loader",
        "unit-cargo-unload-point", "chemical-combustion-chamber", "pyrolysis-generator", "regen-projector", "titan",
        "small-deconstructor", "vent-condenser", "phase-heater", "heat-redirector", "tungsten-wall",
        "tungsten-wall-large", "tank-assembler", "beryllium-wall", "beryllium-wall-large", "eruption-drill",
        "ship-assembler", "mech-assembler", "shield-projector", "beam-link", "world-processor",
        "reinforced-payload-conveyor", "reinforced-payload-router", "disperse", "large-shield-projector",
        "payload-mass-driver", "world-cell", "carbide-wall", "carbide-wall-large", "tank-fabricator", "mech-fabricator",
        "ship-fabricator", "reinforced-surge-wall", "radar", "blast-door", "canvas", "armored-duct", "shield-breaker",
        "unit-repair-tower", "diffuse", "prime-refabricator", "basic-assembler-module", "reinforced-surge-wall-large",
        "tank-refabricator", "mech-refabricator", "ship-refabricator", "slag-heater", "afflict", "shielded-wall",
        "lustre", "scathe", "smite", "underflow-duct", "malign", "shockwave-tower", "heat-source", "flux-reactor",
        "neoplasia-reactor"
    }

    ITEMS: set[str] = {
        "copper", "lead", "metaglass", "graphite", "sand", "coal", "titanium", "thorium", "scrap", "silicon",
        "plastanium", "phase-fabric", "surge-alloy", "spore-pod", "blast-compound", "pyratite", "beryllium",
        "tungsten", "oxide", "carbide"
    }

    LIQUIDS: set[str] = {
        "water", "slag", "oil", "cryofluid", "neoplasm", "arkycite",
        "ozone", "hydrogen", "nitrogen", "cyanogen"
    }

    UNITS: set[str] = {
        "dagger", "mace", "fortress", "scepter", "reign",
        "nova", "pulsar", "quasar", "vela", "corvus",
        "crawler", "atrax", "spiroct", "arkyid", "toxopid",
        "flare", "horizon", "zenith", "antumbra", "eclipse",
        "mono", "poly", "mega", "quad", "oct",
        "risso", "minke", "bryde", "sei", "omura",
        "retusa", "oxynoe", "cyerce", "aegires", "navanax",
        "alpha", "beta", "gamma",

        "stell", "locus", "precept", "vanquish", "conquer",
        "merui", "cleroi", "anthicus", "tecta", "collaris",
        "elude", "avert", "obviate", "quell", "disrupt",
        "evoke", "incite", "emanate"
    }

    EFFECTS: set[str] = {
        "burning", "freezing", "unmoving", "slow", "wet", "melting", "sapped", "electrified", "overdrive", "overclock",
        "shielded", "guardian", "shocked", "blasted", "corroded", "disarmed"
    }

    TEAMS: set[str] = {
        "derelict", "sharded", "crux", "malis"
    }

    SENSABLE: dict[str, Type] = {}
    CONTROLLABLE: dict[str, Type] = {}
