# OpenGPSS Manual (alpha)

## General
Program in OpenGPSS language looks like following:

```
*definition area*
*exit condition*
{{
:executive area
}}
*another definition area if needed*
{{
:another executive area
}}
...
...
```

Definiton area contains definitions of variables, facilities, queues and marks that are used to simulate a system. Every definition line is like:
- For variables:
`type name = initial_value;`
- For structures:
`type name {optional parameters};`

Every separate line in OpenGPSS finishes with ';'. If the line doesn't have ';' at the end, next line is recognized as the continuation of current line.
Comments are C-like:
`// Single line comment`
```
/* Multiline
comment */
```

When simulation is going, exit condition is tested to know when simulation should be stopped. Exit condition should be defined only once:
```
exitwhen(expression with boolean result);
```
When this expression turns to true, simulation will stop.

Double brackets `{{` and `}}` separate executive area from definition area. Executive area is an area where xacts are added and removed, move and process. Executive area contains executive blocks:
```optional_mark_name : executive_block_name(block params);```
assignments to variables or xact parameters (and increments/decrements):
```optional_mark_name : var_name = new_value;```
```optional_mark_name : var_name += expression;```
```optional_mark_name : var_name++;```
and single braces for *try* and *if*/*else_if*/... blocks.
Every line in executive area (except braces) starts with *mark separator* ':', if no mark points to this line, or with name of the mark followed by mark separator. In other words, presence of mark separator in the line means that xact can be transported to this line.
If xact reaches some executive line, it tries to execute it (except single braces and *inject* block - it executes automatically) using its own parameters if needed.

Nearly every parameter - queue/facility name, *wait*/*travel*/*if* parameters - can be not just words, but complex expressions. They will be parsed to a string/number before block execution.


## Language types
- int - simple integer number, value limited by Python language
- float - simple floating point number, value limited by Python language
- string - string (line of characters) with (theoretically) unlimited length. Bounded by "double quotes"
- word - string without quotes, can be used to reach parameters of structure by name of this structure. Often parsed to a string by interpreter

 
## Definition types



## Executive blocks
### inject - add xacts into your system
- Prototype: 
```
:inject(
         string xact_group_name, 
         int time, 
         int timedelta, 
         int initdelay,
         int inject_limit
        ) 
        {
         p1 = int, 
         p5 = int, 
         f1 = float, 
         f8 = float, 
         str1 = string, 
         str3 = string, 
         priority = int/float, 
         custom_name_parameter = string
        };
```
- Usage:

This block will add an xact of group *xact\_group\_name* every *time* beats until it reaches its *inject\_limit*. Xacts will start moving from the line where *inject* block stands. Time between injections can be modified: first xact can be delayed by *initdelay* beats, and *time* parameter can be randomized to *time±timedelta* with even distribution.
{parameters} are optional (if you don't use them, just leave no braces or empty braces). p* are names for integer parameters, f* - for float parameters and str* - for string parameters (their types will be recognized automatically). *priority* is a special number parameter to define priority to xacts. Priority can be used for controlling the order of a processing, etc.
- Example:

```
:inject("main", 10, 4, 0, 250) {p1 = 0, priority = 10};
```
- Additional hacks:

If *inject\_limit* equals zero, there is no limit for this *inject* block.
*timedelta* and *timedelay* also can be zeros.
If *inject\_limit* is positive, but other parameters are zeros, *inject\_limit* xacts will be added simultaneously.
You can also add parameters with custom names, but they are not so good as automatically recognized ones, because a) they can lead to errors because of inattentiveness b) intital values of all of them are automatically turned into strings.

### queue_enter - enter unordered queue to gather statistics
- Prototype:
```
:queue_enter(
             word queue_name
            );
```
