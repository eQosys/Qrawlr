# Qrawlr Grammar Documentation

## Table of Contents
 - [Usage](#usage)
 - [Grammar](#grammar)

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
>text_to_parse = "Hello World"
>grammar = Grammar("example.qgr")
>
>try:
>    parse_tree = grammar.apply_to(text_to_parse, "HelloWorld")
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

### Rule definition

Rules are defined by a header and a body. \
The header consists of the rule name and optional modifiers. \
The body consists of at least one rule option.

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

 - `hidden`: TODO
 - `fuse`: TODO

### Rule option

A rule option is a sequence of matchers. \
The engine will try to match the matchers in the order they are defined. \
Every matcher must be matched for the rule option to be considered matched.

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

### Matcher

A matcher is the smalles unit of a rule option. \
There are 7 types of matchers: \
 - [Any char](#match-any-char)
 - [All](#match-all)
 - [Any](#match-any)
 - [Range](#match-range)
 - [Exact](#match-exact)
 - [Rule](#match-rule)
 - [Stack](#match-stack)

It consists of one of the matcher types, optionally followed by modifiers and/or executors.

>Syntax:
>```qrawlr
>`matcher_type``modifiers``executors`
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

Matches a range of characters.

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

Matches an exact string.

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

Matches the _nth_ item on the specified stack. \
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
If the matcher would normally match, it will not match. \
If the matcher would normally not match, it will match.

If, after inverting, the matcher would match, the matched string will be a single character.

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

The quantifier modifier controls how many times the matcher will match. \
It can be one of the following:
 - `?`: Match 0 or 1 times
 - `*`: Match 0 or more times
 - `+`: Match 1 or more times
 - ``#<`max` ``: Match between 0 and `max-1` times
 - ``#>`min` ``: Match at least `min+1` times
 - ``#`min`-`max` ``: Match between `min` and `max` times

#### Lookahead

The lookahead modifier tells the engine to not consume the matched string. \
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

When the omit match modifier is used, the matched string will not be added to the parse tree.

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

The replace match modifier tells the engine to replace the matched string with the specified content.

The content can be one of the following:
 - ``"`string`"``: Replace with the specified string
 - ``:`stack_name`.`index`:``: Replace with the _nth_ item on the specified stack.
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

### Matcher Executors

Matcher executors are used to execute a limited set of actions when a matcher matches. \
They are always placed directly after the matcher modifiers. (No whitespace in between)

>Syntax:
>```qrawlr
>{`executor1`, `executor2`, ...}
>```
>
>Example:
>```qrawlr
>"Hello"?{ push exampleStack }
>```

#### Push

Pushes the match as a single item on the specified stack.
Omitted matches will not be pushed.

>Syntax:
>```qrawlr
>push `stack_name`
>```
>
>Example:
>```qrawlr
>"Hello"?{ push exampleStack }
>```

#### Pop

Pops the top item from the specified stack.

>Syntax:
>```qrawlr
>pop `stack_name`
>```
>
>Example:
>```qrawlr
>""_{ pop exampleStack }
>```

### Identifier

Identifiers are used for rule names, stack names and match replacement names. \
Only the following characters are allowed in identifiers:
> a-z, A-Z

### Stack

A stack is a list of strings. \
It is used to store matched strings for later use.

### Name collision

Rule names, stack names and match replacement names share the same namespace. \
This means that a rule name cannot be the same as a stack name or match replacement name and vice versa.