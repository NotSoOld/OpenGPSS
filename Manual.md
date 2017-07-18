# OpenGPSS Manual (beta v0.2)

## Navigation
[General](#general)

[Definition types:](#definition-types)

- [Simple variables](#simple-variables)

- [Structure types](#structure-types)

- [Arrays and matrices](#arrays-and-matrices)

- [Conditional functions](#conditional-functions)

[About name ambiguity](#about-name-ambiguity)

[Executive blocks:](#executive-blocks) 

[inject](#inject---add-xacts-into-your-system)
\-- [queue_enter](#queue_enter---enter-unordered-queue-to-gather-statistics)
\-- [queue_leave](#queue_leave---leave-previously-entered-unordered-queue)
\-- [fac_enter](#fac_enter---occupy-facility-by-taking-one-of-its-free-places)
\-- [fac_leave](#fac_leave---free-a-place-in-previously-occupied-facility)
\-- [fac_irrupt](#fac_irrupt---force-into-occupied-facility)
\-- [fac_goaway](#fac_goaway---go-away-from-previously-interrupted-facility)
\-- [fac_avail](#fac_avail---make-facility-available-for-xacts)
\-- [fac_unavail](#fac_unavail---make-facility-closed-for-everyone)
\-- [reject](#reject---delete-xact-entirely-from-system)
\-- [wait](#wait---move-xact-to-fec-for-some-amount-of-time)
\-- [transport/transport_prob/transport_if](#transport-family-blocks---------transport-xact-or-fork-the-path-of-xact)
\-- [if/else_if/else](#ifelse_ifelse---make-xact-follow-different-paths-according-to-some-condition)
\-- [wait_until](#wait_until---block-xact-movement-until-condition-becomes-true)
\-- [chain_enter](#chain_enter---move-xact-to-one-of-user-chains)
\-- [chain_leave](#chain_leave---take-xacts-from-user-chain)
\-- [chain_purge](#chain_purge---take-all-xacts-from-the-user-chain)
\-- [chain_pick](#chain_pick---take-xacts-which-satisfy-a-condition)
\-- [chain_find](#chain_find---take-xacts-from-user-chain-by-index)
\-- [hist_sample](#hist_sample---add-a-sample-to-the-histogram)
\-- [graph_sample](#graph_sample---add-a-sample-x-y-pair-to-the-2d-graph)
\-- [while](#while---do-i-really-need-to-describe-what-it-does-d)
\-- [loop_times](#loop_times---do-something-as-much-times-as-you-need)
\-- [copy](#copy---make-a-full-copy-of-a-xact)
\-- [output](#output---print-something-when-you-need-to)
\-- [xact_report](#xact_report---print-all-information-about-xact-executing-this-block)
\-- [move](#move---just-skip-that-line)
\-- [interrupt](#interrupt---force-interpreter-to-go-to-next-time-beat)
\-- [review_cec](#review_cec---force-interpreter-to-look-through-cec-from-beginning)
\-- [flush_cec](#flush_cec---clear-cec-entirely)
\-- [pause_by_user](#pause_by_user---halt-simulation-until-user-presses-any-key)

[Built-in functions:](#built-in-functions)

- [Random generators](#random-generators)

- [Type converters](#type-converters)

- [find](#find---find-name-of-struct-by-condition-connected-to-structs-parameter)

- [find_minmax](#find_minmax---similar-to-find-but-finds-struct-with-minmax-value-of-its-parameter)

- [Math functions](#math-functions)

## General
Program in OpenGPSS language looks like following:

```
*definition area*
*exit condition*
{{
executive area
}}
*another definition area if needed*
{{
another executive area
}}
...
...
```

Definiton area contains definitions of variables, facilities, queues and marks that are used to simulate a system. Every definition line is like:
- For variables:

`type name = initial_value;`
- For structures:

`type name {initial parameters};`

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

and single braces for *if*/*else_if*/*else*/*while*/*loop_times* blocks.

Xact parameters can be accessed like this:

`xact.p1, xact.str5, xact.p_my_parameter, xact.priority`

(*xact.priority* is a special parameter which is used by interpreter to drive some logic, so every xact has it by default.)

Every line in executive area (except curly braces) can start with name of the mark followed by mark separator. In other words, presence of mark separator in the line means that xact can be transported to this line. Curly braces **cannot** be addressed, it will lead to errors.

If xact reaches some executive line, it tries to execute it (except single curly braces and *inject* block - it executes automatically) using its own parameters if needed.

Nearly every parameter - queue/facility name, *wait*/*travel*/*if* parameters - can be not just words, but complex expressions. They will be parsed to a string/number before block execution. (Except parameters in definitions and *inject* block, because these are parsed before any execution of blocks starts. But initial values for variables and array/matrix size can be expressions.)

Model while simulating has two very important lists: *future events chain*, FEC, and *current events chain*, CEC. Time in model is measured in beats (so, it's discrete). Every beat FEC is watched if there are xacts that need to move in the current beat. If they do, they are moved from FEC to CEC. Then, every xact in CEC is moving through executive blocks until it will be a) rejected from the model b) blocked c) moved to a user chain d) executing *wait* block. 

In case a) xact will be deleted from CEC. 

In case b), which can be caused by trying to enter busy facility or *try* block with failed condition, xact will remain in CEC up to the next beat, in which it tries to move again. 

In case c) xact will be removed from CEC and added to one of user chains.

In case d) xact will be moved to FEC with exit time (time when it needs to move further) set by *wait* block.

New xacts can be added to the model through *inject* and *copy* blocks. Inject block presents an *injector* - it adds one xact to FEC with exit time set according to injector's parameters, and when this xact leaves FEC, it sends a signal to injector that it's time to inject one more xact into FEC. *Copy* block creates copies of xacts which are added into CEC.

There is a special situation called *CEC review*. When interpreter receives a signal "review CEC", it interrupts movement of current xact and starts to go through CEC from its beginning. Blocks like *fac\_leave*, *refresh* and changing xact's *priority* can trigger CEC review (because these actions can affect simulation process. For example, if some xact leaves facility, it becomes available for xacts which wait at *fac\_enter* block but cannot proceed. And when CEC will be reviewed, xacts will be able to move to unlocked facility. Changing of priority may affect the order of xacts' processing.)


## Definition types


**For all types:** 

Name of the variable (as string) can be accessed through dot: *variable.name*.

There is also indirect addressing (tilde sign, "~"), which allows to get the value of variable *which* name is in other variable, for example:
```
str var1 = 'buffered';
int buffered = 5;

~var1++; <== will increment variable "buffered".
```


**Also:**

Current xact (which executes block, assignment, etc.) has some accessible parameters along with its own parameters. They are accessed through dot operator:
```
xact.index
xact.group
```


### Simple variables:

- int

	Just a variable which can hold an integer value and be accessed by its name. Range is the same as range of integer in Python.

	Notes:

	\- If a float value is assigned to int variable, it is implicitly converted to int.

	\- There are three read-only default integer variables which are used by interpreter and can be accessed by user:

	**injected** - count of xacts injected by injectors of the system;

	**rejected** - count of xacts rejected from the system through *reject* blocks;

	**curticks** - how long simulation is going.

- float

	Just a variable which can hold a floating point value and be accessed by its name. Range is the same as range of float in Python.

- str

	Just a variable which can hold a string value and be accessed by its name. Strings can be accessed, assigned and concatenated only.

- bool

	Just a variable which can hold a boolean value (true/false) and be accessed by its name. Boolean variables can be only assigned or accessed.


### Structure types:

- fac (facility)

	This is a device which can be occupied by xacts. Usual practice is to use facility to simulate something that can be occupied by somebody for some amount of time and therefore make other transacts wait until it'll be freed. So, when facility is free (has spare places), xacts can occupy it and move further, but facility is fully busy, xacts will wait until it'll have free places.

	Initial parameters (can be set in curly braces):

	\- isQueued = bool *(default == true)* - if true, this facility will be automatically queued as if there are *queue\_enter* and *queue\_leave* blocks around *fac\_enter* block. Queue will be named with this facility's name.

	\- places = int *(default == 1)* - how many xacts can occupy this facility until it becomes busy.

	Accessible parameters (through dot operator):

	\- curplaces - how many free places are currently available

	\- maxplaces - how many places facility has at all

	\- enters_f - how many xacts entered the facility at this time

	\- isAvail - current availability status of facility

- queue

	This is a device which is generally used for gathering statistics about the flow of transacts near facilities. But queueing can be used not only around *fac\_enter* blocks. Statistics include number of entered xacts, current xacts in the queue, etc. It is important to mention that queues doesn't really sort or queue xacts, it's only gather statistics.

	Initial parameters: none.

	Accessible parameters (through dot operator):

	\- curxacts - how many xacts are currently queued

	\- enters_q - how many xacts entered the queue at this time


- mark

	This is a definition of a transporting mark which can be used in the executive area of a program. When mark is at the left of ':' in the line, it is called a *transporting label*. When mark is present as argument of transport operator (or somewhere else where xacts can be moved around the model), it declares where xact should go, which line it should follow after execution.

	Initial parameters: none.

	Accessible parameters: none.

	Additional notes:

	\- You will always see messages about undefined or unused marks.

- chain

	User chains are used to store transacts here when you need to control their flow through the model. User chains enable user to buffer xacts (and to simulate buffering devices), to release xacts one by one at some point in the model, etc.

	Initial parameters: none.

	Accesible parameters (through dot operator):

	\- length - how many xacts are currently in this user chain

	\- xacts (only available inside find/find\_minmax functions!) - list of current xacts in the chain

- hist<variable_name> (histogram)

	Histograms are one of the ways to gather statistics. Histogram can collect value of a one parameter during simulating. Parameter name is specified in <> brackets after *hist* keyword. Value of this parameter is added to the histogram by calling *hist\_add* block. After simulating, histogram will be printed in both text and pseudo-graphical representations.

	Initial parameters (all of them **must** be set in curly braces):

	\- start - it is first bounding value of histogram

	\- interval - it is a constant interval between histogram marks

	\- count - total number of intervals (excluding interval from -infinity to start and from last mark to +infinity).

	Here is graphical representation of these parameters:

	![alt text](./histillustr.jpg)

	When parameter value is about to be added to histogram, according interval will be chosen. Each interval contains not value of the parameter, but a number of parameter value additions of this interval.

	Accessible parameters (can be accessed thorugh dot operator):

	\- enters_h - how many samples have been added to histogram (weighted)

	\- average - average value of observing parameter


- graph<x_var, y_var> (2D graph)

	Graps are another way of gathering statistics about changes of variables' values. This type allows to gather information in the form of two-dimensional graph (i.e. one value is X, and another is Y on the plot, and they are stored as pairs). According to math laws, every X value can be associated only with one Y value; so, when sampled (X, Y) pair already exists, it will be saved as (X, (oldY + Y) / 2).

	Since plot building is not possible using pseudographics, output of a graph in simulation results will look like table of X-Y pairs, so you can copy them and build plot in Excel, etc.

	Initial parameters: none.

	Accessible parameters: none.


### Arrays and matrices:


Variable of **every** type (simple or structural, except *mark*!) can be defined not as a single variable, but as array:

```
int arr[10] = 0;
queue CPUs[4];
fac CPUs[4] { isQueued = false, places = 1 };
```

or as matrix:

```
float my_matrix[[5, 6]];
bool adjacent[[7, 7]] = false;
```

Initial values specified after "=" or in "{}" will be applied for every array/matrix element. Arrays' length and matrices' width and height are constant (defined only once). Three- and more dimensional arrays are not supported.

Inside, arrays' and matrices' elements are defined as separate objects *(with names like "array_name&&index" and "matrix_name&&(index, index)")* but at the end of simulation they will be printed either with proper names ("array[index]", "matrix[[index, index]]") (for structure types) or definitely as arrays and matrices (for simple types).


### Conditional functions:


These functions which can be defined by user are a feature to replace GPSS's FUNCTION block. There is a word "conditional" in the name, because this function consists of pairs *"condition, result"* and, from first to last, condition of every pair will be evaluated. First condition which occurs to be true will command the interpreter to return result which was in the pair with this condition. 

So, here is a prototype:
```
function function_name(parameters, if any) {
                                            condition1, result1 |
                                            condition2, result2 |
                                            ...
                                            conditionN, resultN
                                           };
```

Every condition is an expression with boolean (or something which can be converted to boolean) result; every result can be an expression. Condition and result are separated by comma, pairs are separated by "|". If no condition succeeds, function will return 0 (if you need to override default behaviour, it's recommended to leave final pair as *"1, value_to_return_if_every_condition_fails"*, so it will be always returned if every other condition failed).

Function also can have some parameters which values will be put to condition and result expression when function will be called. Please **do not** name parameters as your system variables, etc., because then they will be overwritten by function parameters. (But names like "p1" are allowed, even if function uses expressions like "xact.p1".)

Simpliest example of "abs" implementation:
```
function my_abs(value) {
                        value >= 0, value |
                        value < 0, -value     // or "1, -value", because it will always succeed
                       };
```


## About name ambiguity

OpenGPSS is a case-sensitive language. Names can consist of upper and lower register letters, digits (but these names cannot **start** with digit) and underscores.

In some cases identical names are allowed:

\- names of structures with different types can be the same (queue CPU, mark CPU, fac CPU)

\- names of arrays and names of variables can be the same (int myvar, int myvar\[10], int myvar\[\[5, 4]])

But:

\- **do not** name variables with identical words, they'll be messed up (little explanation: structures are either used as blocks' arguments (in this case, their names are parsed as strings, so, there's no big difference what type this structure was of, if name is correct for block) or their accessible parameters are accessed by dot operator (and different parameters have different names for each structure type, as you can mention). And variables can be accessed just like "my\_variable\_name = ...", and you cannot say, what variable is accessed here if you have multiple of them with different types)

\- **never** name any variables/functions/structures as keywords (including "xact", "chxact", "curticks", "injected", "rejected", etc.)

\- Always check that names of your own functions/variables/structures do not match with names of built-in functions and functions from attached modules!

\- Also check that names of modules do not match with keywords or any variables/structures in the system.

Remember, these rules are always a subject to change.


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

{parameters} are optional (if you don't use them, just leave no braces or empty braces). p\* are names for integer parameters, f\* - for float parameters, b\* - for boolean parameters and str\* - for string parameters (their types will be recognized automatically). "\*" can be anything from number to string. *priority* is a special number parameter to define priority to xacts. Priority can be used for controlling the order of a processing, etc. Xact parameters can be accessed using keyword *xact* followed by dot and parameter name.
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

\- Facility name can be an expression with string result (for example, name of one of the facilities) (and you an also do this trick with queue names, chain names, etc. I won't mention it anymore below).

\- This block automatically triggers interpreter to review CEC.

### fac_irrupt - force into occupied facility
- Prototype:
```
fac_irrupt(
           word fac_name,
           int xact_volume (default == 1),
           bool eject (default == false),
           word mark (default == next after this block),
           word elapsedto (default == none)
          );
```
- Usage:

Sometimes you need not to just occupy free facility, but to come into it, stop processing of occupying xacts and/or occupy facility by yourself. For example, a person busy with something can be interrupted from signals or people coming outside. 

So, *fac\_name* can be interrupted by xact with *xact\_volume* (how many places xact needs in facility for itself). If *eject* is false, currently processing xacts will be taken from model chains (CEC, FEC, user chains) and moved to facility interruption chain. When *eject* == false, there are no more arguments. No ejection means that xacts from interruption chain will continue processing after interrupting xact goes away with the help of *fac\_goaway* block. These xacts will process as much time as they have to process when they were interrupted.

When *eject* == true, it means that interrupted xacts will be ejected from this facility and won't return to processing automatically. If *mark* is present, they'll be sent there. If *elapsedto* is present (it is a name of some variable/parameter), elapsed processing time wil be written there.

- Examples:
```
fac_irrupt(CPU, 1, True, to_elapsed, xact.p3);
fac_irrupt(fac, 1, True, '', xact.p1);
fac_irrupt(fac, 3, False);
```

### fac_goaway - go away from previously interrupted facility
- Prototype:
```
fac_goaway(
           word fac_name
          );
```
- Usage:

After you interrupt facility, you need to go away from it (especially when you push some xacts into interrupt chain - otherwise they'll be there forever!). When interrupting xact passes this block, it deletes itself from facility and moves xacts to freed places from interrupt chain.

- Example:
```
fac_goaway(CPU);
```

### fac_avail - make facility available for xacts
- Prototype:
```
fac_avail(
          word fac_name
         );
```
- Usage:

This block has an ability to turn availability status of facility back to "available".

- Example:
```
fac_avail(CPU);
```

- Advanced info:

\- Every facility is available by default.

\- When facility is available, it means in can be entered (if is has free places) and interrupted.

### fac_unavail - make facility closed for everyone
- Prototype:
```
fac_unavail(
            word fac_name
           );
```
- Usage:

Sometimes you need to simulate unavailability of a facility, so that's why this block is implemented.

- Example:
```
fac_unavail(CPU);
```

- Advanced info:

\- When facility is unavailable, it means in **cannot** be entered or interrupted. When facility status turns to "unavailable", it's like facility will be fully busy for incoming xacts (i.e. they will be blocked); xacts processing in this facility will leave it when processing finishes. 

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

These blocks are used to transport xacts from one point in model to another. Transportation can be unconditional (->>), depend on probability (->|) or depend on condition (->?). You can also determine where xacts should go if probability/condition check fails (by default they will just go further through the model).

- Examples:
```
->> CPU_mark;
->| Mark1, 0.4, jmp;
->? mark, xact.pr > 10;
```
- Additional hacks:

\- If you don't like "->" notation, you can use following block names: *transport()*, *transport\_prob()*, *transport\_if()*.

### if/else_if/else - make xact follow different paths according to some condition
- Prototypes:
```
if(
   bool condition
  )
{
	blocks which will be executed in condition == true
}
else_if(
        bool another_condition
       )
{
	blocks which will be executed if another_condition == true
}
else_if...
...
else
{
	what to do if every other chained conditional blocks above failed
}
```
- Usage:

These blocks are used to execute different parts of a program. Choice is made according to conditions in parens - group of blocks in curly braces with a first true condition will be chosen to execute. **Curly braces cannot be omitted!** There can be many *else\_if()* blocks or no of them; also, *else* block can be omitted. Conditional blocks are considered chained and are tested as a whole thing if they are written as in the example, one right after another.

- Examples:
```
if(xact.f3 > 0)
{
	fac_enter(CPU1);
}
else_if(myChain != 3)
{
	fac_enter(CPU2);
}
else
{
	reject(0);
}

if(boolVar)
{
	chain_purge(ch1, toTerm);
}
else
{
	chain_enter(ch1);
}

etc.
```
- Additional hacks:

\- These conditional blocks can be nested. Use them as you'll use them in C or any other similar language.

### wait\_until - block xact movement until condition becomes true
- Prototype:
```
wait_until(
           bool condition
          );
```
- Usage:

Sometimes you don't need xacts to move through special part of program until something happened. So, you can prevent xacts from doing that by using *try* block. If xact enters this block and condition fails, it will remain staying on this block until condition turns to true.

- Example:
```
wait_until(buffer.length > 0);
```

### chain_enter - move xact to one of user chains
- Prototype:
```
chain_enter(
            word chainname
           );
```
- Usage:

User chains are very powerful when you need a mechanism to buffer xacts in one place of the model and, when needed, take them out to another place. This block simply chains xact into *chainname* chain. New xact will be moved from CEC to the end of user chain.

- Example:
```
chain_enter(buffer);
```

### chain_leave - take xacts from user chain
- Prototype:
```
chain_leave(
            word chainname,
            int count,
            word where_to_move (default is next block after that)
           );
```
- Usage:

You can move xacts from user chains back to your model with the help of *chain\_leave* block. *Count* xacts (or less, if there aren't enough xacts in the chain) will be taken from chain *chainname* and moved to the *where\_to\_move* mark in the model (or if there is no mark, they'll be moved one block further after *chain\_leave*).

- Example:
```
chain_leave(buffer, 2, tofacility);
```

### chain_purge - take all xacts from the user chain
- Prototype:
```
chain_purge(
            word chainname,
            word where_to_move (default is next block after that)
           );
```
- Usage:

It is equal to `chain_leave(chain, chain.length, block)`. The chain will be empty after calling this block.

- Example:
```
chain_purge(buffer, killmark);
```

### chain_pick - take xacts which satisfy a condition
- Prototype:
```
chain_pick(
           word chainname,
           condition,
           int count,
           word where_to_move (default - next block after this)
          );
```
- Usage:

While *chain\_leave* gives an opportunity to unconditionally remove xacts from user chains, *chain\_pick* allows to take only xacts which meet specified condition. Condition may look like "chxact.parameter ==/<=/... some value or expression" (it's just an example; left side also may vary). New keyword *chxact* represents xact from user chain which is currently observed (when checking condition, every xacts from user chain will be observed, from first to last). *count* represents how many times should condition be checked; if chain has less "good to go" xacts than *count*, it is OK.

This block is important because it gives a possibility to remove xacts from chains according to their parameters' values, it may be used in some situations (and cannot be made in other way, I think).

- Examples:
```
chain_pick(buffer, chxact.ptime > 10, 3);
chain_pick(buffer, buffer.length > 5, 10, to_kill);
```

### chain_find - take xacts from user chain by index
- Prototype:
```
chain_find(
           word chainname,
           int xact_index,
           int count,
           word where_to_move (default is next block after that)
          );
```
- Usage:

As it is somewhat silly to remove xacts by their index (it is not such parameter which is always important or known), this block is generally used with *find()/find\_minmax()* builtin functions (which return xact index when searching a xact in the user chain). Other behaviour is similar to *chain_pick* block - *count* or less xacts will be removed and every chain xact will be observed through check.

Sometimes this block can be replaced with *chain\_pick* block (and vise versa).

- Example:
```
chain_find(buf, find(buf.xacts.pr < 10), 5);
```

### hist_sample - add a sample to the histogram
- Prototype:
```
hist_sample(
            word histogram_name,
	    int weight (default == 1)
           );
```
- Usage:

This block, when executed, adds a sample (i.e. a value of parameter which is tracked by *histogram\_name* histogram) to the specified histogram. Weight is a simple multiplier (how much samples should this particular sample be counted as).

- Example:
```
hist_sample(buffer_hist);
```

### graph_sample - add a sample (X-Y pair) to the 2D graph
- Prototype:
```
graph_sample(
             word graph_name
            );
```
- Usage:

This block, when executed, adds a sample to the specified 2D graph (i.e. it evaluates graph X and Y parameters and adds a pair of these values to the graph's values' table).

- Example:
```
graph_sample(time_queuelength_dependency);
```

### while - do I really need to describe what it does..? :D
- Prototype:
```
while(
      bool condition
     )
{
	blocks which will be executed while condition is true
}
```
- Usage:

This block will make xact loop through some blocks in curly braces while condition in parens is true. When it turns to false, xact will move further. Be aware of infinite loops!

- Example:
```
while(count > 0)
{
	wait(4);
	count += 1;
}
```
- Additional hacks:

\- This block can also be nested.

\- The process of iterating can be controlled by two blocks: *iter\_next* and *iter\_stop* (without empty parens after name). *Iter\_next* forces xact to go to the next iteration and *iter\_stop* forces xact to stop iterating at all (like *continue* and *break* in C).

### loop_times - do something as much times as you need
- Prototype:
```
loop_times(
           word iterator,
           int upper_border
          )
{
	blocks which will be executed while iterator value is less than upper_border
}
```
- Usage:

This block will make xact loop through some blocks in curly braces while *iterator* (it is the name of some variable or xact parameter) value is less than *upper\_border* value. Iterator will be incremented automatically before every loop. **Un**like in other languages, you can change both iterator and upper border values while cycling, but, **like** in other languages, it can lead to awkward situations when done wrong.

Inside loop *iterator* will consequently take values from its initial value to *upper\_border* minus 1. After exiting loop, iterator value will be equal to *upper\_border*.

- Example:
```
loop_times(xact.p1, 10)
{
	output("Xact p1 value is "+to_str(xact.p1));
}
```
- Additional hacks:

\- This block can also be nested.

\- The process of iterating can be controlled by two blocks: *iter\_next* and *iter\_stop* (without empty parens after name). *Iter\_next* forces xact to go to the next iteration and *iter\_stop* forces xact to stop iterating at all (like *continue* and *break* in C).

### copy - make a full copy of a xact
- Prototype:
```
copy(
     int copies_count,
     word where_to_go (default == next to this block)
    );
```
- Usage:

This block will make *copies\_count* copies of a xact which is executing this block. If *where\_to\_go* mark is present, copies will be sent there. Every parameter will be copied except unique xact index.

- Example:
```
copy(4, tobuf);
```
- Additional hacks:

\- This block is useful in certain situations as it immediately adds xacts to the system with known group and parameters. Use it as an advantage.

### output - print something when you need to
- Prototype:
```
output(
       int/float/bool/string output
      );
```
- Usage:

If you need to print some values, info, debug messages while xacts are moveing throuth model, use this block. When xact will execute it, output message will be printed. Xact will simply move one line down. Output will be in such format: *(current time, current line, current xact index): your string*.

- Example:
```
output("Xact p1 value is "+to_str(xact.p1));
```
- Additional hacks:

\- Output string can be a whole expression with string (!) result or a simple number/boolean value.

### xact_report - print all information about xact executing this block
- Prototype:
```
xact_report();
```
- Usage:

This block will print all information about xact which is executing this block right now: group, index, line of code, all parameters including priority. You can use this for statistics gathering or debugging.

### move - just skip that line
- Prototype:
```
move();
```
- Usage:

When xact meets this block, it just moves to next line. That's all.

This block is generally used inside other blocks in the interpreter, but you can also write it as some "foo" block in line which cannot be omitted but shouldn't do anything.

### interrupt - force interpreter to go to next time beat
- Prototype:
```
interrupt();
```
- Usage:

When executed, this block will send signal to interpreter to stop looking through CEC and just move to next time beat (which leads to taking some xacts from FEC if it's their time to leave and looking CEC from beginning).

### review_cec - force interpreter to look through CEC from beginning
- Prototype:
```
review_cec();
```
- Usage:

Just like *interrupt*, this block sends a signal to interpreter. CEC will be reviewed in the same time beat (interpreter won't move to next time beat).

- Additional hacks:

\- Following blocks automatically call *review\_cec* inside them: *fac\_leave*, *fac\_goaway* and *reject* (and also every assignment to *xact.pr* parameter).

### flush_cec - clear CEC entirely
- Prototype:
```
flush_cec();
```
- Usage:

While *reject* presents a common and right way to delete xacts from model, *flush\_cec* simply and rudely annihilates all xacts from CEC. Calling this block might be very dangerous for model's health. Facilities and queues are checked if they contain executing xact (but nothing is done for xacts which are deleted!). Of course, after executing this block, current xact will stop its life too, and entirely system will halt until something arrives to CEC from FEC.

### pause_by_user - halt simulation until user presses any key
- Prototype:
```
pause_by_user(
              string message (default == none)
             );
```
- Usage:

After executing this block, interpreter will wait until user presses any key to continue. If *message* is present, it will be printed. You can use this block among with *output* and *xact\_report* blocks while debugging.


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

### find() - find name of struct by condition connected to struct's parameter
- Prototype:
```
find(
     condition (looks like "structure.parameter ? expression")
     );
```
- Usage:

In situations where you need to know name of free facility, chain with known length, etc., *find()* can help you.

First word at the left of conditional expression is "facilities"/"queues"/"chains"/"chains.xacts"; second word after dot can be any available parameter name for according structure. According to first word, return value will differ: if you search for a facility/queue/chain, it will be a structure name (and "", if nothing was found); if you search for xact in chain, it will be xact index (and -1, if nothing was found).

- Examples:
```
find(facilities.curplaces > 0) ==> returns name of facility
find(chains.length < 10) ==> returns name of chain
find(chains.xacts.p2 == 5) ==> returns xact index
```

### find_minmax() - similar to find(), but finds struct with min/max value of its parameter
- Prototype:
```
find_minmax(
            word min/max,
            name of the structure and its parameter
           );
```
- Usage:

This function acts as *find()* function, but it doesn't actually operates with a condition. Instead, it will execute search of a structure (in the range of given names, for example, *facilities.curplaces*) to end up with a structure with minimal or maximal value of its parameter. Again, return value depends on what search do you perform.

- Examples:
```
find_minmax(max, facilities.curplaces) ==> returns name of the facility
find_minmax(min, chains.length) ==> returns name of the chain
find_minmax(max, chains.xacts.pr) ==> returns index of xact
```

### Math functions:
- abs\_value(number) - returns an absolute value of int/float number.
- exp\_distr(x, lambda) - returns value of a cumulative exponential distribution function with given x and lambda (more on [Wikipedia](https://en.wikipedia.org/wiki/Exponential_distribution#Cumulative_distribution_function)). Is useful when setting processing times, etc.
- round\_to(value, digits) - returns *value* rounded to floating number with *digits* digits after point (*digits* default value = 0).
