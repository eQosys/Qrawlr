# Qrawlr Grammar Documentation


## Table of Contents
<details>
<summary>Click to expand</summary>

  - [Usage](#usage)
    - [Example](#example)
  - [Grammar](#grammar)
    - [Comments](#comments)
    - [Rule definition](#rule-definition)
      - [Rule modifiers](#rule-modifiers)
    - [Rule option](#rule-option)
    - [Matcher](#matcher)
      - [Match any char](#match-any-char)
      - [Match all](#match-all)
      - [Match any](#match-any)
      - [Match range](#match-range)
      - [Match exact](#match-exact)
      - [Match rule](#match-rule)
      - [Match stack](#match-stack)
    - [Matcher Modifiers](#matcher-modifiers)
      - [Invert](#invert)
      - [Quantifier](#quantifier)
      - [Lookahead](#lookahead)
      - [Omit match](#omit-match)
      - [Replace match](#replace-match)
    - [Action Triggers](#action-triggers)
    - [Matcher Actions](#matcher-actions)
      - [Action Push](#action-push)
      - [Action Pop](#action-pop)
      - [Action Message](#action-message)
      - [Action Fail](#action-fail)
    - [Identifier](#identifier)
    - [Stack](#stack)
    - [Name collision](#name-collision)
    - [Escape sequences](#escape-sequences)

</details>

---

## Usage

### Example

`example.qgr`
>```qrawlr
>HelloWorld:
>    Prefix " "_ Postfix
>
>Prefix:
>   "Hello"
>
>Postfix:
>    [ 'az' 'AZ' ]+
>```

`example.py`
>```python
>from Grammar import Grammar, GrammarException
>
>grammar = Grammar("example.qgr")
>text_to_parse = "Hello World"
>entry_point = "HelloWorld"
>
>try:
>    parse_tree = grammar.apply_to(text_to_parse, entry_point)
>except GrammarException as e:
>    print(e)
>else:
>    if parse_tree is None:
>        print("Failed to parse text")
>    elif parse_tree.length < len(text_to_parse):
>        print("Failed to parse entire text")
>    else:
>        print("Successfully parsed text")
>```

---

## Grammar

### Comments

At the moment, only single-line comments are supported. \
Comments _must_ start with `\\` at the beginning of a line and end at the end of the same line.

>Syntax:
>```qrawlr
>\\`comment`
>```
>
>Example:
>```qrawlr
>\\ This is a comment
>```

---

### Rule definition

Rules are defined by a header and a body. \
The header consists of the rule name and optional [modifiers](#rule-modifiers). \
The body consists of at least one [rule option](#rule-option).

The engine will try to match the rule options in the order they are defined. \
After a rule option has been matched, the entire rule is considered matched and the engine will return to the parent rule.

Rule names follow the same rules as [identifiers](#identifier)

>Syntax:
>```qrawlr
>\\ Rule without modifiers
>`rule_name`:
>    `rule_option`
>    ...
>
>\\ Rule with modifiers
>`rule_name`(`modifier1` `modifier2` ...):
>    `rule_option`
>    ...
>```
>
>Example:
>```qrawlr
>\\ Rule without modifiers. Matches either "Hello" or "World"
>Rule:
>    "Hello"
>    "World"
>
>\\ Rule with modifiers. Matches "Hello"
>Rule(fuse):
>    "Hel" "lo"
>```

#### Rule modifiers

  - `hidden`: The matched content will be added directly to the parent.
  - `fuse`: All consecutive strings will be fused into a single string. (e.g. "Hel" "lo" -> "Hello")

---

### Rule option

A rule option is a sequence of [matchers](#matcher). \
A rule option is treated as if surrounded by parenthesis denoting a [match all](#match-all) matcher.

>Syntax:
>```qrawlr
>`matcher1` `matcher2` ...
>```
>
>Example:
>```qrawlr
>\\ Rule option with 2 matchers. Matches "HelloWorld"
>Rule:
>    "Hello" "World"

---

### Matcher

A matcher is the smallest unit of a [rule option](#match-option). \
There are 7 types of matchers:
  - [Any char](#match-any-char)
  - [All](#match-all)
  - [Any](#match-any)
  - [Range](#match-range)
  - [Exact](#match-exact)
  - [Rule](#match-rule)
  - [Stack](#match-stack)

It consists of one of the matcher types, optionally followed by [modifiers](#matcher-modifiers) and/or [action-triggers](#action-triggers).

>Syntax:
>```qrawlr
>`matcher_type``modifiers``actions`
>```
>
>Example:
>```qrawlr
>"Hello"?{ push exampleStack }
>```

#### Match any char

Matches any character.

>Syntax:
>```qrawlr
>.
>```

#### Match all

Contains a list of matchers. \
Matches all of them in the order they are defined.

>Syntax:
>```qrawlr
>(`matcher1` `matcher2` ...)
>```
>
>Example:
>```qrawlr
>( "Hello" "World" )
>```

#### Match any

Contains a list of matchers. \
The engine will try to match the matchers in the order they are defined. \
If one of the matchers matches, the entire matcher is considered matched and all other matchers are ignored.

>Syntax:
>```qrawlr
>[`matcher1` `matcher2` ...]
>```
>
>Example:
>```qrawlr
>[ "Hello" "World" ]
>```

#### Match range

Matches an inclusive range of characters. \
[Escape sequences](#escape-sequences) are supported.

>Syntax:
>```qrawlr
>'`start_char``end_char`'
>```
>
>Example:
>```qrawlr
>'az'
>```

#### Match exact

Matches an exact string. \
[Escape sequences](#escape-sequences) are supported.

>Syntax:
>```qrawlr
>"`string`"
>```
>
>Example:
>```qrawlr
>"Hello"
>```

#### Match rule

Matches a rule.

>Syntax:
>```qrawlr
>`rule_name`
>```
>
>Example:
>```qrawlr
>Rule
>```

#### Match stack

Matches the _nth_ item on the specified [stack](#stack). \
If the index is out of bounds, the matcher will always match with an empty string. \
Index 0 denotes the top of the stack. (Last item pushed)

>Syntax:
>```qrawlr
>:`stack_name`.`index`:
>```
>
>Example:
>```qrawlr
>:exampleStack.0:
>```

---

### Matcher Modifiers

Matcher modifiers control the behavior of a matcher. \
They are always placed directly after the matcher type. (No whitespace in between)

The modifiers must be placed in the following order:
 1. [Invert](#invert)
 2. [Quantifier](#quantifier)
 3. [Lookahead](#lookahead)
 4. [Omit match](#omit-match)
 5. [Replace match](#replace-match)


#### Invert

Inverts the matcher. \
If the matcher would normally match, it will not match and vice versa. \
If, after inverting, the matcher would match, the matched item will be a single character.

>Syntax:
>```qrawlr
>`matcher`!
>```
>
>Example:
>```qrawlr
>"Hello"!
>```

#### Quantifier

The quantifier modifier controls how many times the matcher will match.

It can be one of the following:
  - `?`: Match 0 or 1 times
  - `*`: Match 0 or more times
  - `+`: Match 1 or more times
  - ``#`exact` ``: Match exactly `exact` times
  - ``#`min`-`max` ``: Match between `min` and `max` times
  - ``#<`max` ``: Match between 0 and `max-1` times
  - ``#>`min` ``: Match at least `min+1` times

#### Lookahead

The lookahead modifier tells the engine to not consume the matched item. \
This means that the matched string will be available for other (following) matchers to match.

>Syntax:
>```qrawlr
>`matcher`~
>```
>
>Example:
>```qrawlr
>"Hello"~
>```

#### Omit match

When the omit match modifier is used, the matched item will not be added to the parse tree.

>Syntax:
>```qrawlr
>`matcher`_
>```
>
>Example:
>```qrawlr
>"Hello"_
>```

#### Replace match

The replace match modifier tells the engine to replace the matched item with the specified content.

The content can be one of the following:
  - ``"`string`"``: Replace with the specified string. [Escape sequences](#escape-sequences) are supported.
  - ``:`stack_name`.`index`:``: Replace with the _nth_ item on the specified [stack](#stack).
  - `` `name` ``: Give the matched string a name. Use the [omit match modifier](#omit-match) to not add the matched string to the parse tree.

>Syntax:
>```qrawlr
>`matcher`->`content`
>```
>
>Example:
>```qrawlr
>"Hello"->"World"
>"Foo"->:exampleStack.0:
>"Bar"_->ParsedBar
>```

---

### Action Triggers

Action triggers are used to execute [actions](matcher-actions) on specific events. \
They are always placed directly after the [matcher modifiers](#matcher-modifiers). (No whitespace in between)
When a trigger has only one action, the brackets for the action list can be omitted.

Triggers can be on of the following:
  - `onMatch`: Executes the specified actions when the matcher matches.
  - `onFail`: Executes the specified actions when the matcher fails to match.

**Note**: `onMatch` also triggers when any subsequent matcher fails to match. It does not guarantee that the match will be present in the final parse tree. \
Example: Applying `"H"{ onMatch: message("Matched 'H') } "ello"` on `Hell` will print `Matched 'H'` even though the entire rule fails to match.

>Syntax:
>```qrawlr
>`matcher`{`trigger1`: `actionList1`, `trigger2`: `actionList2`, ...}
>```
>
>Example:
>```qrawlr
>"Hello"?{ onMatch: push(_, exampleStack), onFail: [ message("Hello user!"), fail("Expected 'Hello'") ] }
>```

---

### Matcher Actions

Matcher actions are used to execute a limited set of actions when a trigger is activated.

Actions can be one of the following:
  - [`push`](#action-push)
  - [`pop`](#action-pop)
  - [`message`](#action-message)
  - [`fail`](#action-fail)

Action arguments can be one of the following:
  - `"string"`: A string. [Escape sequences](#escape-sequences) are supported.
  - `identifier`: An [identifier](#identifier).
  - `_`: Represents the matched string.

>Syntax:
>```qrawlr
>`action`(`arg1`, `arg2`, ...)
>```
>
>Example:
>```qrawlr
>push(_, exampleStack)
>```

#### Action Push

Pushes the match as a single item on the specified stack.
[Omitted matches](#omit-match) will not be pushed.

>Syntax:
>```qrawlr
>push(`string_to_push`, `stack_name`)
>```
>
>Example:
>```qrawlr
>push(_, exampleStack)
>```

#### Action Pop

Pops the top item from the specified stack.

>Syntax:
>```qrawlr
>pop(`stack_name`)
>```
>
>Example:
>```qrawlr
>pop(exampleStack)
>```

#### Action Message

Prints the specified message along with the current position in the text to the console and continues parsing.

>Syntax:
>```qrawlr
>message(`message`)
>```
>
>Example:
>```qrawlr
>message("Hello user!")
>```
>==> MSG: file.qgr:1:1: Hello user!

#### Action Fail

Stops the parsing process and prints the specified message along with the current position in the text.

>Syntax:
>```qrawlr
>fail(`message`)
>```
>
>Example:
>```qrawlr
>fail("Expected 'Hello'")
>```
>==> FAIL: file.qgr:1:1: Expected 'Hello'

---

### Identifier

Identifiers are used for [rule](#rule-definition) names, [stack](#stack) names and [match replacement](#replace-match) names. \
Only the following characters are allowed in identifiers:
> a-z, A-Z

---

### Stack

A stack is a list of strings. \
Each stack has a unique name assigned. \
Stacks are created implicitly when referencing them via a [match stack](#match-stack) or an [executor](#matcher-executors). \
It is used to store matched strings for later use.

---

### Name collision

[Rule](#rule-definition) names, [stack](#stack) names and [match replacement](#replace-match) names share the same namespace. \
This means that a rule name cannot be the same as a stack name or match replacement name and vice versa.

---

### Escape sequences

Escape sequences are used to escape special characters in strings. \
Supported escape sequences are:
  - `\a`: Bell
  - `\b`: Backspace
  - `\e`: Escape character
  - `\f`: Form feed
  - `\n`: Newline
  - `\r`: Carriage return
  - `\t`: Horizontal tab
  - `\v`: Vertical tab
  - `\\`: Backslash
  - `\'`: Single quote
  - `\"`: Double quote
  - `\xhh`: Hexadecimal character code
