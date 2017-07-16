# OpenGPSS - Инструкция (бета 0.2)

## Содержание
[Основное]()

[Объявление переменных и структур:]()

- [Простые переменные]()

- [Структурные типы]()

[О неоднозначности имён]()

[Исполняемые блоки:]()

[inject](#inject---add-xacts-into-your-system)
\-- [queue_enter](#queue_enter---enter-unordered-queue-to-gather-statistics)
\-- [queue_leave](#queue_leave---leave-previously-entered-unordered-queue)
\-- [fac_enter](#fac_enter---occupy-facility-by-taking-one-of-its-free-places)
\-- [fac_leave](#fac_leave---free-a-place-in-previously-occupied-facility)
\-- [fac_irrupt](#fac_irrupt---force-into-occupied-facility)
\-- [fac_goaway](#fac_goaway---go-away-from-previously-interrupted-facility)
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
\-- [hist_add](#hist_add---add-a-sample-to-the-histogram)
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

[Встроенные функции:]()

- [Генераторы случайных чисел]()

- [Конвертеры типов]()

- [find()]()

- [find_minmax()]()

- [Математические функции]()

## Основное
Программа на языке OpenGPSS выглядит следующим образом:

```
*область определения переменных*
*условие выхода*
{{
исполняемая область
}}
*опциональная область определения переменных*
{{
еще одна исполняемая область
}}
и т.д.
```

Область определения содержит определения переменных и структур (устройств, очередей, меток и т.д.), которые используются при имитации системы. Каждая линия определения примерно выглядит так:
- для переменных:

`тип имя = начальное значение;`
- для структур:

`тип имя {начальные параметры};`

Каждая строка в OpenGPSS заканчивается точкой с запятой. Если в конце строки нет точки с запятой, это значит, что эта же строка продолжается на следующей линии (т.е. можно записывать длинные строки в несколько линий).
Комментарии - как в Си:
`// Это однострочный комментарий`
```
/* А это - многострочный
комментарий */
```

Во время имитации условие выхода проверяется в конце каждого такта, чтобы убедиться, не пора ли прекращать имитацию модели. Условие выхода определяется ОДИН раз:

`exitwhen(выражение с булевым результатом);`

Когда выражение станет истинно, имитация закончится.

Двойные фигурные скобки `{{` и `}}` отделяют область определения от исполняемой области. Исполняемая область - это область перемещения транзактов, их добавления и удаления, обработки и т.д. Исполняемая область содержит исполняемые блоки:

`необяз.имя_метки : имя_блока(параметры блока);`

присвоения переменным или параметрам транзактов (++/-- также считаются за присвоения):

`необяз.имяметки : имя_переменной = новое_значение/выражение;`

`необяз.имяметки : имя_переменной++;`

и одиночные скобки для блоков *if*/*else_if*/*else*/*while*/*loop_times*.

К параметрам транзактов можно обратиться через точку:

`xact.p1, xact.str5, xact.p_my_parameter, xact.priority`

(*priority*, приоритет - это специальный параметр, который по умолчанию есть у каждого транзакта; он используется интерпретатором для имитации модели)

Любая исполняемая строка может начинаться с метки (после которой стоит двоеточие - разделитель). Если метка присутствует, это значит, что транзакт можно переместить на этот блок, зная имя метки. **НЕЛЬЗЯ** адресовать метками одиночные фигурные скобки, это приведет к ошибкам (адресуйте блоки до или после них).

Если транзакт достигает какой-нибудь исполняемой строки, он пытается выполнить ее (кроме фигурных скобок и блока *inject* - последний исполняется автоматически время от времени), при этом, если блоку нужны какие-либо параметры транзакта, испольуются параметры именно исполняющего транзакта.

Практически каждый параметр (за исключением специально оговоренных случаев) - имя структуры, выражения в условиях - могут быть не просто словами-строками, а целыми выражениями любой сложности (с операторами +, -, \*, /, ** (возведение в степень), % (остаток от деления), ~ (косвенная адресация) и встроенными функциями). Они будут превращены в значения перед вызовом блока. (исключение - начальные значения параметров, в том числе блока *inject*, т.к. они передаются "как есть", без проверки на выражение. Размеры массивов и начальные значения переменных могут быть выражениями.).

В модели во время имитации есть два важных списка (цепи): *цепь будущих событий*, ЦБС, и *цепь текущих событий*, ЦТС.
