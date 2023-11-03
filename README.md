# mlog++

[![Run Unit Tests](https://github.com/albi-c/mlogpp/actions/workflows/test.yml/badge.svg?branch=master)](https://github.com/albi-c/mlogpp/actions/workflows/test.yml)

statically typed high level mindustry logic language

## Installation:
`pip install mlogpp`

## Usage:
`python -m mlogpp <file(s) to compile> [options]`

### Options:
* `-o:f`, `--output-file` - output to file
* `-o:s`, `--output-stdout` - output to stdout
* `-o:c`, `--output-clip` - output to clipboard (default)
* `-v`, `--verbose` - output more information
* `-l`, `--lines` - print line numbers when output is stdout
* `-a`, `--assembly` - compile as mlog++ assembly
* `-V`, `--version` - print version and exit

## Examples:
### Hello, World:
```javascript
Block message1
print("Hello, World!")
printflush(message1)
```
Prints `Hello, World!`

### Constants:
```javascript
const x = 5
const let y = "constant"
const num a, b
a = 5
b = 3
```

### For loops:
```javascript
for (num i = 1; i < 11; i += 1) {
    print(i)
    if (i < 10) {
        print(", ")
    }
}

Block message1
printflush(message1)
```
Prints `1, 2, 3, 4, 5, 6, 7, 8, 9, 10`

### Ranges:
```javascript
for (i : 1..5) {
    print(i + 1)
    print(" ")
}

Block message1
printflush(message1)
```
Prints `2 3 4 5`

### Functions:
```javascript
function length(num x, num y) -> num {
    return sqrt(x * x + y * y)
}

print(length(3, 4))

Block message1
printflush(message1)
```
Prints `5`

### Memory cell access:
```javascript
Block cell1, message1
cell1[0] = 10
print(cell1[0])
printflush(message1)
```
Prints `10`

### Subcommands:
```javascript
ubind(@mega)
ucontrol.move(@thisx, @thisy)
```
Makes all `@mega` units move to the processor

### Scopes:
```javascript
num a = 0

# use let for type inference
let b = 0

function test(num x) {
    let a = x
    b = x
}

test(10)

print(a)
print(" ")
print(b)

Block message1
printflush(message1)
```
Prints `0 10`

### Structures:
```javascript
Block message1

struct Vec2 {
    num x
    num y
}

let vec = Vec2(10, 20)

vec.x += 5

print(vec.x)
print(" ")
print(vec.y)

printflush(message1)
```
Prints `15 20`

### Assembly:
```javascript
${LOOP_LENGTH = 2 + 3}

i = 0
loop_start:
    i += 1
    
    print(i)
    print("\n")
    
    :loop_start (i < ${LOOP_LENGTH})

Block message1
printflush(message1)
```
Prints `1 2 3 4 5`

### Longer examples can be found in `examples/`

## Features:
* variables \
  `num x = 1`
* type inference \
  `let x = 2`
* constants \
  `const x = 2`  
  `const num y = 3`  
  `const let z = 5`
* types 
  * `num`, `str`
  * `Block`, `Unit`,
  * `BlockType`, `UnitType`, `ItemType`, `LiquidType`,
  * `Controller`, `Team`
* comments \
  `# comment`
* memory cell access \
  `cell1[0] = cell1[1]`
* functions \
  `function f(num x, num y) -> num { return x + y }`
* subcommands \
  `ucontrol.move(1, 2)`
* if / else \
  `if (a == b) { print("a") } else { print("b") }`
* while loops \
  `while (a > b) { b += 1 }`
* for loops \
  `for (num i = 0; i < 10; i += 1) { print(i) }`
* ranges \
  `for (i : 5) { print(i) }`
* break / continue
* native functions \
  `ubind(@mega)`
* constants \
  `const VALUE = 30`
* inline python subset \
  `${x = 7 ^ 2}`  
  `print(${y = x // 2})`  
  `${"cell" + x}[0] = y`
* output from builtin functions directly to new variables (can be constants) \
  `ulocate.building(core, true, x: num, y: num, building: const Block)`
* structures with inheritance \
  `struct Vec2 { num x, y }`  
  `struct Vec3 : Vec2 { num z }`
* colors for effects \
  `effect.hit(x, y, %_35adc8)`

## Native functions:
* read `result`, `cell`, `position`
    * Read data from `cell` at `position` to `result`
* write `data`, `cell`, `position`
    * Write `data` to `cell` at `position`
* draw `operation`, `arg0` ... `arg5`
    * Add a draw `operation` to the draw buffer
    * Operations:
        * clear `red`, `green`, `blue`
        * color `red`, `green`, `blue`, `alpha`
        * stroke `width`
        * line `x1`, `y1`, `x2`, `y2`
        * rect `x`, `y`, `width`, `height`
        * lineRect `x`, `y`, `width`, `height`
        * poly `x`, `y`, `sides`, `radius`, `rotation`
        * linePoly  `x`, `y`, `sides`, `radius`, `rotation`
        * triangle `x1`, `y1`, `x2`, `y2`, `x3`, `y3`
        * image `x`, `y`, `image`, `size`, `rotation`
* drawflush `display`
    * Flush the draw buffer to `display`
* print `message`
    * Add `message` to the draw buffer
* printflush `message`
    * Flush the draw buffer to `message`
* getlink `result`, `n`
    * Put the `n`th link to `result`
* control `command`, `block`, `arg0` ... `arg2`
    * Control `block`
    * Commands:
        * enabled `block`, `enabled`
        * shoot `block`, `x`, `y`, `shoot`
        * shootp `block`, `unit`, `shoot`
        * config `block`, `configuration`
        * color `block`, `red`, `green`, `blue`
* radar `filter0` ... `filter2`, `sort`, `block`, `order`, `result`
    * Find a unit near `block` and store it in `result`
    * Filters:
        * any
        * enemy
        * ally
        * player
        * attacker
        * flying
        * boss
        * ground
    * Sort:
        * distance
        * health
        * shield
        * armor
        * maxHealth
* sensor `result`, `block`, `parameter`
    * Get `parameter` of `block` and store it in `result`
* op `operation`, `result`, `op0`, `op1`
    * Perform a mathematical operation
    * Operations:
        * Basic: add, sub, mul, div, idiv (integer division), mod, pow, lessThan, lessThanEq, greaterThan, greaterThanEq, max, min, abs, log, log10, floor, ceil, sqrt, sin, cos, tan, asin, acos, atan, equal, notEqual
        * Bitwise: shl (shift left), shr (shift right), or, and, xor, not
        * Special:
            * strictEqual - doesn't coerce types
            * land - logic and
            * angle - angle of vector
            * len - length of vector
            * noise - simplex noise
            * rand - random number
* wait `time`
    * Wait `time` seconds
* lookup `type`, `result`, `id`
    * Look up `type` by `id`
    * Types:
        * block
        * unit
        * item
        * liquid
* end
    * End the program
* jump `position`, `condition`, `op0`, `op1`
    * Jump to `position` if `condition` is met
    * Conditions:
        * equal
        * notEqual
        * lessThan
        * lessThanEq
        * greaterThan
        * greaterThanEq
        * strictEqual
        * always
* ubind `type`
    * Bind next unit of type `type` and store it in `@unit`
* ucontrol `command`, `op0` ... `op4`
    * Control the bound unit
    * Commands:
        * idle
        * stop
        * move `x`, `y`
        * approach `x`, `y`, `radius`
        * boost `enable`
        * pathfind
        * target `x`, `y`, `shoot`
        * targetp `unit`, `shoot`
        * itemDrop `to`, `amount`
        * itemTake `from`, `item`, `amount`
        * payDrop
        * payTake `takeUnits`
        * mine `x`, `y`
        * flag `value`
        * build `x`, `y`, `block`, `rotation`, `configuration`
        * getBlock `x`, `y`, `type`, `building`
        * within `x`, `y`, `radius`, `result`
* uradar `filter0` ... `filter2`, `sort`, `___`, `order`, `result`
    * Same as radar, except `block` is replaced by `@unit`
* ulocate `type`, `arg0` ... `arg2`, `outx`, `outy`, `found`, `building`
    * Locate block of type `type`
    * Types:
        * ore `___`, `___`, `oreType`
        * building `group`, `enemy`, `___`
        * spawn `___`, `___`, `___`
        * damaged `___`, `___`, `___`
    * Building groups:
        * core
        * storage
        * generator
        * turret
        * factory
        * repair
        * rally
        * battery
        * reactor

* mathematical functions (replacement for `op`):
    * mod
    * pow
    * and, or, xor, not
    * max, min
    * abs
    * log, log10
    * ceil, floor
    * sqrt
    * sin, cos, tan
    * asin, acos, atan
