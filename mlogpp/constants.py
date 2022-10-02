from .value import Type


# block names inside of logic processors
BLOCKS = set("""\
    siliconSmelter, siliconCrucible, kiln, graphitePress, plastaniumCompressor, multiPress, phaseWeaver,
    surgeSmelter, pyratiteMixer, blastMixer, cryofluidMixer,
    melter, separator, disassembler, sporePress, pulverizer, incinerator, coalCentrifuge,

    powerSource, powerVoid, itemSource, itemVoid, liquidSource, liquidVoid, payloadSource, payloadVoid, illuminator, heatSource,
    
    copperWall, copperWallLarge, titaniumWall, titaniumWallLarge, plastaniumWall, plastaniumWallLarge, thoriumWall, thoriumWallLarge, door, doorLarge,
    phaseWall, phaseWallLarge, surgeWall, surgeWallLarge,
    
    mender, mendProjector, overdriveProjector, overdriveDome, forceProjector, shockMine,
    scrapWall, scrapWallLarge, scrapWallHuge, scrapWallGigantic, thruster,
    
    conveyor, titaniumConveyor, plastaniumConveyor, armoredConveyor, distributor, junction, itemBridge, phaseConveyor, sorter, invertedSorter, router,
    overflowGate, underflowGate, massDriver,
    
    mechanicalPump, rotaryPump, impulsePump, conduit, pulseConduit, platedConduit, liquidRouter, liquidContainer, liquidTank, liquidJunction, bridgeConduit, phaseConduit,
    
    combustionGenerator, thermalGenerator, steamGenerator, differentialGenerator, rtgGenerator, solarPanel, largeSolarPanel, thoriumReactor,
    impactReactor, battery, batteryLarge, powerNode, powerNodeLarge, surgeTower, diode,
    
    mechanicalDrill, pneumaticDrill, laserDrill, blastDrill, waterExtractor, oilExtractor, cultivator,
    
    coreShard, coreFoundation, coreNucleus, vault, container, unloader,
    
    duo, scatter, scorch, hail, arc, wave, lancer, swarmer, salvo, fuse, ripple, cyclone, foreshadow, spectre, meltdown, segment, parallax, tsunami,
    
    groundFactory, airFactory, navalFactory,
    additiveReconstructor, multiplicativeReconstructor, exponentialReconstructor, tetrativeReconstructor,
    repairPoint, repairTurret,
    
    payloadConveyor, payloadRouter, payloadPropulsionTower,
    
    message, switchBlock, microProcessor, logicProcessor, hyperProcessor, largeLogicDisplay, logicDisplay, memoryCell, memoryBank,
    canvas,
    
    launchPad, interplanetaryAccelerator
""".replace(" ", "").replace("\n", "").split(","))

# block names inside the Mindustry code
BLOCK_IDS = set("""\
    graphite-press, multi-press, silicon-smelter, silicon-crucible, kiln, plastanium-compressor, phase-weaver,
    surge-smelter, cryofluid-mixer, pyratite-mixer, blast-mixer, melter, separator, disassembler, spore-press,
    pulverizer, coal-centrifuge, incinerator,
    
    copper-wall, copper-wall-large, titanium-wall, titanium-wall-large, plastanium-wall, plastanium-wall-large,
    thorium-wall, thorium-wall-large, phase-wall, phase-wall-large, surge-wall, surge-wall-large, door, door-large,
    
    mender, mend-projector, overdrive-projector, overdrive-dome, force-projector,
    
    conveyor, titanium-conveyor, plastanium-conveyor, armored-conveyor, junction, bridge-conveyor, phase-conveyor,
    sorter, inverted-sorter, router, distributor, overflow-gate, underflow-gate, mass-driver,
    
    mechanical-pump, rotary-pump, impulse-pump, conduit, pulse-conduit, plated-conduit, liquid-router, liquid-container,
    liquid-tank, liquid-junction, bridge-conduit, phase-conduit,
    
    power-node, power-node-large, surge-tower, diode, battery, large-battery, combustion-generator, thermal-generator,
    steam-generator, differential-generator, rtg-generator, solar-panel, solar-panel-large, thorium-reactor,
    impact-reactor,
    
    mechanical-drill, pneumatic-drill, laser-drill, airblast-drill, water-extractor, cultivator, oil-extractor,
    
    core-shard, core-foundation, core-nucleus, container, vault, unloader,
    
    duo, scatter, scorch, hail, wave, lancer, arc, parallax, swarmer, salvo, segment, tsunami, fuse, ripple, cyclone,
    foreshadow, spectre, meltdown,
    
    ground-factory, air-factory, naval-factory, additive-reconstructor, multiplicative-reconstructor,
    exponential-reconstructor, tetrative-reconstructor, repair-point, repair-turret, payload-conveyor, payload-router,
    payload-propulsion-tower,
    
    illuminator, launch-pad, interplanetary-accelerator,
    
    message, switch, micro-processor, logic-processor, hyper-processor, memory-cell, memory-bank, logic-display,
    logic-display-large
""".replace(" ", "").replace("\n", "").split(","))

# block link names
BLOCK_LINKS = set()
for name in BLOCK_IDS:
    if "-" in name:
        spl = name.split("-")

        # filter out "large" from names
        if len(spl) >= 2 and spl[-1] == "large":
            name = spl[-2]

        else:
            name = spl[-1]

    BLOCK_LINKS.add(name)

ITEMS = set("""\
    scrap, copper, lead, graphite, coal, titanium, thorium, silicon, plastanium,
    phaseFabric, surgeAlloy, sporePod, sand, blastCompound, pyratite, metaglass
""".replace(" ", "").replace("\n", "").split(","))

LIQUIDS = set("""\
    water, slag, oil, cryofluid
""".replace(" ", "").replace("\n", "").split(","))

UNITS = set("""\
    dagger, mace, fortress, scepter, reign,
    nova, pulsar, quasar, vela, corvus,
    crawler, atrax, spiroct, arkyid, toxopid,
    
    flare, horizon, zenith, antumbra, eclipse,
    mono, poly, mega, quad, oct,
    
    risso, minke, bryde, sei, omura,
    retusa, oxynoe, cyerce, aegires, navanax
""".replace(" ", "").replace("\n", "").split(","))

TEAMS = {"derelict", "sharded", "crux", "malis", "green", "blue"}

# values readable by the sensor command
SENSOR_READABLE = {
    "totalItems": Type.NUM,
    "firstItem": Type.NUM,
    "totalLiquids": Type.NUM,
    "totalPower": Type.NUM,
    "itemCapacity": Type.NUM,
    "liquidCapacity": Type.NUM,
    "powerCapacity": Type.NUM,
    "powerNetStored": Type.NUM,
    "powerNetCapacity": Type.NUM,
    "powerNetIn": Type.NUM,
    "powerNetOut": Type.NUM,
    "ammo": Type.NUM,
    "ammoCapacity": Type.NUM,
    "health": Type.NUM,
    "maxHealth": Type.NUM,
    "heat": Type.NUM,
    "efficiency": Type.NUM,
    "progress": Type.NUM,
    "timescale": Type.NUM,
    "rotation": Type.NUM,
    "x": Type.NUM,
    "y": Type.NUM,
    "shootX": Type.NUM,
    "shootY": Type.NUM,
    "size": Type.NUM,
    "dead": Type.NUM,
    "range": Type.NUM,
    "shooting": Type.NUM,
    "boosting": Type.NUM,
    "mineX": Type.NUM,
    "mineY": Type.NUM,
    "mining": Type.NUM,
    "speed": Type.NUM,
    "team": Type.TEAM,
    "type": Type.BLOCK_TYPE,
    "flag": Type.NUM,
    "controlled": Type.CONTROLLER,
    "controller": Type.BLOCK | Type.UNIT,
    "name": Type.NUM,
    "payloadCount": Type.NUM,
    "payloadType": Type.NUM,
    "enabled": Type.NUM,
    "config": Type.NUM,
    "color": Type.NUM
} | {
    item: Type.NUM for item in ITEMS
} | {
    liquid: Type.NUM for liquid in LIQUIDS
}

# values writable by "." access
CONTROLLABLE = {
    "enabled", "config", "color"
}
