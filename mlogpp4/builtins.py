from .values import Type, VariableValue

BUILTINS = {
    "@this": VariableValue("@this", Type.BLOCK, True),
    "@thisx": VariableValue("@thisx", Type.NUM, True),
    "@thisy": VariableValue("@thisy", Type.NUM, True),
    "@ipt": VariableValue("@ipt", Type.NUM, True),
    "@counter": VariableValue("@counter", Type.NUM, True),
    "@links": VariableValue("@links", Type.NUM, True),
    "@unit": VariableValue("@unit", Type.UNIT, False),
    "@time": VariableValue("@time", Type.NUM, True),
    "@tick": VariableValue("@tick", Type.NUM, True),
    "@second": VariableValue("@second", Type.NUM, True),
    "@minute": VariableValue("@minute", Type.NUM, True),
    "@waveNumber": VariableValue("@waveNumber", Type.NUM, True),
    "@waveTime": VariableValue("@waveTime", Type.NUM, True),
    "@mapw": VariableValue("@mapw", Type.NUM, True),
    "@maph": VariableValue("@maph", Type.NUM, True),

    "true": VariableValue("true", Type.NUM, True),
    "false": VariableValue("false", Type.NUM, True),
    "null": VariableValue("null", Type.NULL, True),

    "@ctrlProcessor": VariableValue("@ctrlProcessor", Type.CONTROLLER, True),
    "@ctrlPlayer": VariableValue("@ctrlPlayer", Type.CONTROLLER, True),
    "@ctrlCommand": VariableValue("@ctrlCommand", Type.CONTROLLER, True),

    "@solid": VariableValue("@solid", Type.BLOCK_TYPE, True)
}
