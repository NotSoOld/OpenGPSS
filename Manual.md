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
`// This is single line comment`
```
/* And this is multiline
comment */
```

When simulation is going, exit condition is tested to know when simulation should be stopped. Exit condition should be defined only once:

`exitwhen(expression with boolean result);`

When this expression turns to true, simulation will stop.

Double brackets `{{` and `}}` separate executive area from definition area. Executive area is an area where xacts are added and removed, move and process. Executive area contains executive blocks:

`optional_mark_name:executive_block_name(block params);`

assignments to variables or xact parameters (and increments/decrements):

`optional_mark_name:var_name = new_value;`

`optional_mark_name:var_name += expression;`

`optional_mark_name:var_name++;`

and single braces for *try* and *if*/*else_if*/... blocks.

Every line in executive area (except curly braces) starts with name of the mark followed by mark separator. In other words, presence of mark separator in the line means that xact can be transported to this line. Curly braces **cannot** be addressed, it will lead to errors.

If xact reaches some executive line, it tries to execute it (except single curly braces and *inject* block - it executes automatically) using its own parameters if needed.

Nearly every parameter - queue/facility name, *wait*/*travel*/*if* parameters - can be not just words, but complex expressions. They will be parsed to a string/number before block execution. (Except parameters in definitions and *inject* block, because these are parsed before any execution of blocks starts.)

Model while simulating has two very important lists: *future events chain*, FEC, and *current events chain*, CEC. Time in model is measured in beats (so, it's discrete). Every beat FEC is watched if there are xacts that need to move in the current beat. If they do, they are moved from FEC to CEC. Then, every xact in CEC is moving through executive blocks until it will be a) rejected from the model b) blocked c) moved to a user chain d) executing *wait* block. 

In case a) xact will be deleted from CEC. 

In case b), which can be caused by trying to enter busy facility or *try* block with failed condition, xact will remain in CEC up to the next beat, in which it tries to move again. 

In case c) xact will be removed from CEC and added to one of user chains.

In case d) xact will be moved to FEC with exit time (time when it needs to move further) set by *wait* block.

New xacts can be added to the model through *inject* and *copy* blocks. Inject block presents an *injector* - it adds one xact to FEC with exit time set according to injector's parameters, and when this xact leaves FEC, it sends a signal to injector that it's time to inject one more xact into FEC. *Copy* block creates copies of xacts which are added into CEC.

There is a special situation called *CEC review*. When interpreter receives a signal "review CEC", it interrupts movement of current xact and starts to go through CEC from its beginning. Blocks like *fac\_leave*, *refresh* and changing xact's *priority* can trigger CEC review (because these actions can affect simulation process. For example, if some xact leaves facility, it becomes available for xacts which wait at *fac\_enter* block but cannot proceed. And when CEC will be reviewed, xacts will be able to move to unlocked facility. Changing of priority may affect the order of xacts' processing.)


## Language types
- int - simple integer number, value limited by Python language
- float - simple floating point number, value limited by Python language
- string - string (line of characters) with (theoretically) unlimited length. Bounded by "double quotes"
- word - string without quotes, can be used to reach parameters of structure by name of this structure. Often parsed to a string by interpreter or is needed for parser's work.

 
## Definition types
### Simple variables:
- int

Just a variable which can hold an integer value and be accessed by its name. Range is the same as range of integer in Python.

Notes:

\- If a float value is assigned to int variable, it is implicitly converted to int.

\- There are three read-only default integer variables which are used by interpreter and can be accessed by user:

injected - count of xacts injected by injectors of the system;

rejected - count of xacts rejected from the system through *reject* blocks;

curticks - how long simulation is going.

- float

Just a variable which can hold a floating point value and be accessed by its name. Range is the same as range of float in Python.

- str

Just a variable which can hold a string value and be accessed by its name. Strings can be accessed, assigned and concatenated only.

- bool

Just a variable which can hold a boolean value (true/false) and be accessed by its name. Boolean variables can be only assigned or accessed.

### Structure types:
- fac (facility)

This is a device which can be occupied by xacts. Usual practice is to use facility to simulate something that can be occupied by somebody for some amount of time and therefore make other transacts wait until it'll be freed. So, when facility is free (has spare places), xacts can occupy it and move further, but facility is fully busy, xacts will wait until it'll have free places.

Parameters (can be set in curly braces):
\- isQueued = bool *(default == true)* - if true, this facility will be automatically queued as if there are *queue\_enter* and *queue\_leave* blocks around *fac\_enter* block. Queue will be named with this facility's name.

\- places = int *(default == 1)* - how many xacts can occupy this facility until it becomes busy.

- queue

This is a device which is generally used for gathering statistics about the flow of transacts near facilities. But queueing can be used not only around *fac\_enter* blocks. Statistics include number of entered xacts, current xacts in the queue, etc. It is important to mention that queues doesn't really sort or queue xacts, it's only gather statistics.

Parameters: none.

- mark

This is a definition of a transporting mark which can be used in the executive area of a program. When mark is at the left of ':' in the line, it is called a *transporting label*. When mark is present as argument of transport operator (or somewhere else where xacts can be moved around the model), it declares where xact should go, which line it should follow after execution.

Parameters: none.

Additional notes:

\- You will always see messages about undefined or unused marks.

- chain

User chains are used to store transacts here when you need to control their flow through the model. User chains enable user to buffer xacts (and to simulate buffering devices), to release xacts one by one at some point in the model, etc.

Parameters: none.


## Executive blocks
### inject - add xacts into your system
- Prototype: 
```
inject(
         string xact_group_name, 
         int time, 
         int timedelta, 
         int initdelay,
         int inject_limit
        ) 
        {
         p1 = int,
         f1 = float, 
         str1 = string, 
         b1 = bool, 
         priority = int/float (default == 0), 
         custom_name_parameter = string
        };
```
- Usage:

This block will add an xact of group *xact\_group\_name* every *time* beats until it reaches its *inject\_limit*. Xacts will start moving from the line where *inject* block stands. Time between injections can be modified: first xact can be delayed by *initdelay* beats, and *time* parameter can be randomized to *time±timedelta* with even distribution.

{parameters} are optional (if you don't use them, just leave no braces or empty braces). p\* are names for integer parameters, f\* - for float parameters, b\* - for boolean parameters and str\* - for string parameters (their types will be recognized automatically). "\*" can be anything from number to string. *priority* is a special number parameter to define priority to xacts. Priority can be used for controlling the order of a processing, etc.
- Example:
```
inject("main", 10, 4, 0, 250) {p1 = 0, priority = 10};
```
- Additional hacks:

\- If *inject\_limit* equals zero, there is no limit for this *inject* block.

\- *timedelta* and *timedelay* also can be zeros.

\- If *inject\_limit* is positive, but other parameters are zeros, *inject\_limit* xacts will be added simultaneously.

\- You can also add parameters with custom names, but they are not so good as automatically recognized ones, because a) they can lead to errors because of inattentiveness b) intital values of all of them are automatically turned into strings.

### queue_enter - enter unordered queue to gather statistics
- Prototype:
```
queue_enter(
             word queue_name
            );
```
- Usage:

This block will queue executing xact in the queue *queue\_name*.

- Example:
```
queue_enter(CPU);
```
- Additional hacks:

\- Queue name can be an expression with string result (for example, name of one of the queues).

### queue_leave - leave previously entered unordered queue
- Prototype:
```
queue_leave(
             word queue_name
            );
```
- Usage:

This block will remove current xact from queue *queue\_name*. If xact will try to leave queue which it didn't enter, an error will be raised.

- Example:
```
queue_leave(CPU);
```
- Additional hacks:

\- Queue name can be an expression with string result (for example, name of one of the queues).

### fac_enter - occupy facility by taking one of its free places
- Prototype:
```
fac_enter(
          word fac_name,
          int xact_volume (default == 1)
         );
```
- Usage:

This block is used to simulate a facility which can be occupied by some number of xacts. If facility *fac\_name* has free places, xact will move further and will be present in facility's busyness list. If facility is fully busy, xact will stop at this block and will try to enter this facility again every beat until it proceeds. Xact can occupy more than one facility 'seat', it can be set by *xact\_volume* argument.

*fac\_enter* is usually queued by *queue\_enter* and *queue\_leave* blocks to gather iformation about how long xacts wait to enter busy facility and how much of them are waiting.

- Example:
```
fac_enter(CPU);
```
- Additional hacks:

\- Facility name can be an expression with string result (for example, name of one of the facilities).

\- Facilities can be automatically queued (so, you won't need to write queueing blocks manually) as if it is *queue\_enter* block right above *fac\_enter* block and *queue\_leave* block right under *fac\_enter* block.

### fac_leave - free a place in previously occupied facility
- Prototype:
```
fac_leave(
          word fac_name
         );
```
- Usage:

This block will free a place in facility *fac\_name*, triggering CEC review to give an ability to blocked xacts to occupy freed facility. If the facility was not previously occupied by leaving xact, an error will be raised.

- Example:
```
fac_leave(CPU);
```
- Additional hacks:

\- Facility name can be an expression with string result (for example, name of one of the facilities).

\- This block automatically triggers interpreter to review CEC.

### reject - delete xact entirely from system
- Prototype:
```
reject(
       int reject_counter_inc
      );
```
- Usage:

This block is used to delete xacts from system. It means that xact will not move through model anymore and will be erased from CEC. *reject\_counter\_inc* defines how much should be added to reject counter default variable.

- Example:
```
reject(1);
```
- Additional hacks:

\- If you are so inattentive that you send xacts to block *reject* which are in some facilities/queues, interpreter will automatically erase these xacts from corresponding facilities/queues.

\- This block automatically triggers interpreter to review CEC (because of previous hack - after deleting xact from facility this facility can be occupied by other xacts).

### wait - move xact to FEC for some amount of time
- Prototype:
```
wait(
     int time_to_wait,
     int time_delta (default == 0)
    );
```
- Usage:

This block is used to simulate processing of a xact. It moves xact to FEC (preventing it from moving through model immediately) setting its exit time to *time\_to\_wait±time\_delta* (with even distribution).

- Example:
```
wait(8, 3);
```

### transport family blocks ("->>", "->|", "->?") - transport xact or fork the path of xact
- Prototypes:
```
->> word markname;
->| word markname_if_true, 
    float probability, 
    word markname_if_false (default == block next to this block)
->? word markname_if_true,
    expression condition,
    word markname_if_false (default == block next to this block)
```
- Usage:

These blocks are used to transport xacts from one point in model to another. Transportation can be unconditional (*->>*), depend on probability (*->|*) or depend on condition (*->?*). You can also determine where xacts should go if probability/condition check fails (by default they will just go further through the model).

- Examples:
```
->> CPU_mark;
->| Mark1, 0.4, jmp;
->? mark, xact.pr > 10;
```
- Additional hacks:

\- If you don't like "->" notation, you can use block names as following: *transport()*, *transport\_prob()*, *transport\_if()*.



## Built-in functions
### Random generators:
- random_int(min, max) - generates a pseudo-random integer between *min* and *max*, including min and max values.
- random_float(min, max) - generates a pseudo-random floating point value *min* <= value <= *max*.
- random01() - generates a pseudo-random float value between 0 and 1 (like probability).

### Type converters:
- to_str(val) - tries to convert *val* into string and returns string.
- to_int(val) - tries to convert *val* into integer and returns integer. Can raise "cannot convert" error.
- to_float(val) - tries to convert *val* into floating point number and returns it. Can raise "cannot convert" error.
- to_bool(val) - tries to convert *val* into boolean value (true/false). Following values can be converted: true/false boolean values, "true"/"false" strings, any numbers (==0 - false, !=0 - true); otherwise, error will be raised.
